#!/usr/bin/env python3
#
# =============================================================================
#  Project      : MIDI Studio
#  Description  : MIDI player and MIDI-to-MP3 converter for Linux (FluidSynth + FFmpeg)
#  Author       : Raffaele Catapano
#  License      : MIT (see LICENSE)
#  Created on   : 11/11/2026
#  Version      : 1.0
#
#  Copyright (c) 2025-2026 Raffaele Catapano
#  Released under the MIT License - see the LICENSE file for details.
#  SPDX-License-Identifier: MIT
# =============================================================================
"""synth_backend.py - audio engine of MIDI Studio (Linux).

MIDI -> WAV synthesis through FluidSynth (with access to almost every synthesis
setting that matters for sound quality) and WAV -> MP3 conversion through FFmpeg
in high quality.

No third-party Python dependencies: only external executables (fluidsynth,
ffmpeg) called through subprocess.

This module never produces human-readable text. Progress messages and errors
are reported as message keys plus parameters, which the GUI translates
(see i18n.py):
  - log_callback(key, **params)
  - BackendError.key / BackendError.detail

FluidSynth settings reference: fluidsynth(1) and
https://www.fluidsynth.org/api/settings_synth.html
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

# --------------------------------------------------------------------------
# Constants / enums taken from the official FluidSynth documentation
# --------------------------------------------------------------------------

MIDI_EXTENSIONS = {".mid", ".midi", ".kar", ".rmi"}
SOUNDFONT_EXTENSIONS = {".sf2", ".sf3", ".SF2", ".SF3"}
SOUNDFONT_ENV = "MIDI_SOUNDFONT"

# fluid_interp enum (synth.h): NONE=0, LINEAR=1, 4th order (default)=4, 7th/sinc=7.
# Keys are i18n message keys (translated by the GUI), values are the FluidSynth ids.
INTERPOLATION_METHODS: Dict[str, int] = {
    "interp_none": 0,
    "interp_linear": 1,
    "interp_4th": 4,
    "interp_7th": 7,
}
DEFAULT_INTERPOLATION = 7  # for offline rendering the CPU is not a constraint

CHORUS_TYPES: Dict[str, int] = {
    "chorus_sine": 0,
    "chorus_triangle": 1,
}

MIDI_BANK_SELECT_MODES = ["gs", "gm", "xg", "mma"]

# Sample formats for file rendering (audio.file.format).
# 'float' avoids any quantization before the MP3 conversion.
AUDIO_FILE_FORMATS = ["s16", "s24", "s32", "float", "double"]

COMMON_SOUNDFONT_DIRS = [
    Path("/usr/share/soundfonts"),
    Path("/usr/share/sounds/sf2"),
    Path("/usr/share/sounds/sf3"),
    Path("/usr/local/share/soundfonts"),
    Path("/usr/local/share/fluidsynth"),
    Path.home() / ".local" / "share" / "soundfonts",
    Path.home() / "soundfonts",
]


# --------------------------------------------------------------------------
# Errors
# --------------------------------------------------------------------------

class ToolNotFoundError(RuntimeError):
    """A required external tool is not in the PATH (the message is the tool name)."""


class BackendError(RuntimeError):
    """Error with a translatable message key and a technical detail (tool output)."""

    def __init__(self, key: str, detail: str = ""):
        super().__init__(f"{key}: {detail}" if detail else key)
        self.key = key
        self.detail = detail


class RenderError(BackendError):
    pass


class ConvertError(BackendError):
    pass


# --------------------------------------------------------------------------
# Synthesizer settings (FluidSynth) - they cover the main parameters that
# really affect the timbre (e.g. the "realism" of a piano)
# --------------------------------------------------------------------------

@dataclass
class ReverbSettings:
    active: bool = True
    room_size: float = 0.2   # [0.0 - 1.0] FluidSynth default
    damping: float = 0.0     # [0.0 - 1.0]
    width: float = 0.5       # [0.0 - ~100], 0-1 recommended
    level: float = 0.9       # [0.0 - 1.0]


@dataclass
class ChorusSettings:
    active: bool = True
    voice_count: int = 3     # synth.chorus.nr, default 3
    level: float = 2.0       # synth.chorus.level, default 2.0
    speed_hz: float = 0.3    # synth.chorus.speed, default 0.3 Hz
    depth_ms: float = 8.0    # synth.chorus.depth, default 8.0 ms
    mod_type: int = 0        # 0 = sine, 1 = triangle (ignored by FluidSynth >= 2.2)


@dataclass
class SynthSettings:
    soundfont: Optional[str] = None
    sample_rate: float = 48000.0        # synth.sample-rate [22050-96000]
    gain: float = 0.6                   # synth.gain [0-10], FluidSynth default 0.2
    polyphony: int = 256                # synth.polyphony [1-65535]
    interpolation: int = DEFAULT_INTERPOLATION
    cpu_cores: int = field(default_factory=lambda: max(1, (os.cpu_count() or 2)))
    audio_channels: int = 1             # synth.audio-channels (stereo pairs)
    midi_bank_select: str = "gs"
    audio_file_format: str = "float"    # sample format of the intermediate WAV
    reverb: ReverbSettings = field(default_factory=ReverbSettings)
    chorus: ChorusSettings = field(default_factory=ChorusSettings)

    def clone(self) -> "SynthSettings":
        return SynthSettings(
            soundfont=self.soundfont,
            sample_rate=self.sample_rate,
            gain=self.gain,
            polyphony=self.polyphony,
            interpolation=self.interpolation,
            cpu_cores=self.cpu_cores,
            audio_channels=self.audio_channels,
            midi_bank_select=self.midi_bank_select,
            audio_file_format=self.audio_file_format,
            reverb=ReverbSettings(**asdict(self.reverb)),
            chorus=ChorusSettings(**asdict(self.chorus)),
        )

    def fingerprint(self) -> tuple:
        """Hashable tuple: used to know whether a rendering must be redone."""
        return (
            self.soundfont, round(self.sample_rate), round(self.gain, 3),
            self.polyphony, self.interpolation, self.cpu_cores,
            self.audio_channels, self.midi_bank_select, self.audio_file_format,
            self.reverb.active, round(self.reverb.room_size, 3),
            round(self.reverb.damping, 3), round(self.reverb.width, 3),
            round(self.reverb.level, 3),
            self.chorus.active, self.chorus.voice_count,
            round(self.chorus.level, 3), round(self.chorus.speed_hz, 3),
            round(self.chorus.depth_ms, 3), self.chorus.mod_type,
        )


# Presets designed for a natural "solo" instrument (e.g. piano): a long hall
# reverb tail, almost no chorus (chorus slightly detunes the sound: nice for
# pads/strings but unnatural for an acoustic piano), maximum interpolation.
def preset_realistic_piano(base: SynthSettings) -> SynthSettings:
    s = base.clone()
    s.interpolation = 7
    s.gain = 0.55
    s.reverb.active = True
    s.reverb.room_size = 0.35
    s.reverb.damping = 0.25
    s.reverb.width = 0.7
    s.reverb.level = 0.35
    s.chorus.active = False
    s.audio_file_format = "float"
    return s


def preset_default(base: SynthSettings) -> SynthSettings:
    s = base.clone()
    s.interpolation = 7
    s.gain = 0.6
    s.reverb = ReverbSettings()
    s.chorus = ChorusSettings()
    s.audio_file_format = "float"
    return s


def preset_low_resources(base: SynthSettings) -> SynthSettings:
    s = base.clone()
    s.interpolation = 1
    s.polyphony = 64
    s.reverb.active = False
    s.chorus.active = False
    s.audio_file_format = "s16"
    s.sample_rate = 44100.0
    return s


# --------------------------------------------------------------------------
# MP3 conversion settings (FFmpeg / libmp3lame)
# --------------------------------------------------------------------------

@dataclass
class Mp3Settings:
    mode: str = "vbr"                 # "vbr" or "cbr"
    vbr_quality: int = 0              # 0 (best) .. 9 (worst), LAME -q:a
    cbr_bitrate: str = "320k"
    sample_rate: int = 44100          # standard MP3: up to 48000
    high_quality_resample: bool = True  # use the soxr resampler when available
    normalize_loudness: bool = False    # loudnorm EBU R128 (single pass)
    title_tag: Optional[str] = None
    artist_tag: Optional[str] = None


# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------

def find_tool(name: str) -> Path:
    tool = shutil.which(name)
    if tool is None:
        raise ToolNotFoundError(name)
    return Path(tool)


def tools_available() -> Dict[str, Optional[str]]:
    return {
        "fluidsynth": shutil.which("fluidsynth"),
        "ffmpeg": shutil.which("ffmpeg"),
    }


def list_soundfonts(extra_dirs: Optional[List[Path]] = None) -> List[Path]:
    """List the SoundFonts found in all known locations, without duplicates."""
    dirs = list(COMMON_SOUNDFONT_DIRS)
    if extra_dirs:
        dirs.extend(extra_dirs)

    env_sf = os.environ.get(SOUNDFONT_ENV)
    found: List[Path] = []
    seen = set()

    if env_sf:
        p = Path(env_sf).expanduser()
        if p.is_file() and p not in seen:
            found.append(p)
            seen.add(p)

    for directory in dirs:
        if not directory.is_dir():
            continue
        for ext in ("*.sf2", "*.SF2", "*.sf3", "*.SF3"):
            for f in sorted(directory.glob(ext)):
                rf = f.resolve()
                if rf not in seen and rf.is_file():
                    found.append(rf)
                    seen.add(rf)
    return found


def is_midi_file(path: Path) -> bool:
    return path.suffix.lower() in MIDI_EXTENSIONS


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


# --------------------------------------------------------------------------
# FluidSynth command line
# --------------------------------------------------------------------------

def _fluidsynth_option_flags(settings: SynthSettings) -> List[str]:
    """Translate SynthSettings into '-o key=value' flags for fluidsynth."""
    r = settings.reverb
    c = settings.chorus

    opts = [
        f"synth.gain={settings.gain:.3f}",
        f"synth.polyphony={int(settings.polyphony)}",
        f"synth.cpu-cores={int(settings.cpu_cores)}",
        f"synth.audio-channels={int(settings.audio_channels)}",
        f"synth.midi-bank-select={settings.midi_bank_select}",
        f"synth.sample-rate={settings.sample_rate:.1f}",
        f"synth.reverb.active={1 if r.active else 0}",
        f"synth.reverb.room-size={r.room_size:.3f}",
        f"synth.reverb.damp={r.damping:.3f}",
        f"synth.reverb.width={r.width:.3f}",
        f"synth.reverb.level={r.level:.3f}",
        f"synth.chorus.active={1 if c.active else 0}",
        f"synth.chorus.nr={int(c.voice_count)}",
        f"synth.chorus.level={c.level:.3f}",
        f"synth.chorus.speed={c.speed_hz:.3f}",
        f"synth.chorus.depth={c.depth_ms:.3f}",
        f"synth.chorus.type={int(c.mod_type)}",
        f"audio.file.format={settings.audio_file_format}",
    ]
    flags: List[str] = []
    for opt in opts:
        flags += ["-o", opt]
    return flags


def build_fluidsynth_command(
    fluidsynth: Path,
    soundfont: Path,
    midi: Path,
    wav_out: Path,
    settings: SynthSettings,
    include_audio_file_driver: bool = True,
    commands_file: Optional[Path] = None,
) -> List[str]:
    cmd = [str(fluidsynth), "-ni"]
    if include_audio_file_driver:
        cmd += ["-a", "file"]
    cmd += ["-T", "wav", "-F", str(wav_out), "-r", str(int(settings.sample_rate))]
    cmd += ["-g", f"{settings.gain:.3f}"]
    # The interpolation method is not a FluidSynth setting: it can only be chosen
    # with the shell command 'interp <n>'. With '-i' (no shell) fluidsynth does
    # not read stdin, so the command is placed in a command file loaded with '-f'.
    if commands_file is not None:
        cmd += ["-f", str(commands_file)]
    cmd += _fluidsynth_option_flags(settings)
    cmd += [str(soundfont), str(midi)]
    return cmd


def render_wav(
    fluidsynth: Path,
    soundfont: Path,
    midi: Path,
    wav_out: Path,
    settings: SynthSettings,
    log_callback=None,
) -> None:
    """Synthesize the MIDI file to WAV with FluidSynth, applying every setting.

    The interpolation method (not a loadable FluidSetting) is applied through a
    small command file passed with '-f' (see build_fluidsynth_command).
    """
    if not soundfont.is_file():
        # FluidSynth would silently render an empty (silent) WAV
        raise RenderError("err_soundfont_missing", str(soundfont))
    if log_callback:
        log_callback("be_starting")

    commands_file = wav_out.with_suffix(".fscmd")
    commands_file.write_text(f"interp {int(settings.interpolation)}\n", encoding="utf-8")
    failures: List[str] = []

    try:
        for include_file_driver in (True, False):
            cmd = build_fluidsynth_command(
                fluidsynth, soundfont, midi, wav_out, settings,
                include_file_driver, commands_file,
            )

            # Up to 10 attempts: every time a failure is due to a '-o' parameter
            # unknown to the installed FluidSynth version, that parameter is
            # removed and the rendering is retried (unavailable settings are
            # simply ignored, they never block the use of the program).
            for _attempt in range(10):
                if wav_out.exists():
                    try:
                        wav_out.unlink()
                    except OSError:
                        pass

                proc = _run(cmd)

                if proc.returncode == 0 and wav_out.exists() and wav_out.stat().st_size > 44:
                    if log_callback:
                        log_callback("be_render_done")
                    return

                unknown = set(re.findall(r"Setting parameter '([^']+)' not found", proc.stderr))
                if unknown:
                    new_cmd = []
                    skip_next = False
                    for i, tok in enumerate(cmd):
                        if skip_next:
                            skip_next = False
                            continue
                        if tok == "-o" and i + 1 < len(cmd) and cmd[i + 1].split("=", 1)[0] in unknown:
                            skip_next = True
                            continue
                        new_cmd.append(tok)
                    if new_cmd != cmd:
                        if log_callback:
                            log_callback("be_param_ignored", params=", ".join(sorted(unknown)))
                        cmd = new_cmd
                        continue

                failures.append(
                    f"$ {' '.join(cmd)}\nexit={proc.returncode}\nSTDERR:\n{proc.stderr}\nSTDOUT:\n{proc.stdout}"
                )
                break
    finally:
        try:
            commands_file.unlink()
        except OSError:
            pass

    raise RenderError("err_render", "\n---\n".join(failures))


# --------------------------------------------------------------------------
# WAV -> MP3 conversion with FFmpeg (high quality)
# --------------------------------------------------------------------------

def _build_ffmpeg_cmd(
    ffmpeg: Path,
    wav_in: Path,
    mp3_out: Path,
    settings: Mp3Settings,
    use_soxr: bool,
) -> List[str]:
    cmd = [str(ffmpeg), "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav_in)]

    filters = []
    if use_soxr:
        filters.append("aresample=resampler=soxr:precision=28")
    if settings.normalize_loudness:
        filters.append("loudnorm=I=-14:TP=-1.0:LRA=11")

    if filters:
        cmd += ["-af", ",".join(filters)]

    cmd += ["-vn", "-ar", str(settings.sample_rate), "-ac", "2", "-c:a", "libmp3lame"]

    if settings.mode == "cbr":
        cmd += ["-b:a", settings.cbr_bitrate]
    else:
        cmd += ["-q:a", str(settings.vbr_quality)]

    if settings.title_tag:
        cmd += ["-metadata", f"title={settings.title_tag}"]
    if settings.artist_tag:
        cmd += ["-metadata", f"artist={settings.artist_tag}"]

    cmd += [str(mp3_out)]
    return cmd


def convert_wav_to_mp3(
    ffmpeg: Path,
    wav_in: Path,
    mp3_out: Path,
    settings: Mp3Settings,
    log_callback=None,
) -> None:
    mp3_out.parent.mkdir(parents=True, exist_ok=True)

    attempts = [True, False] if settings.high_quality_resample else [False]
    failures: List[str] = []

    for use_soxr in attempts:
        cmd = _build_ffmpeg_cmd(ffmpeg, wav_in, mp3_out, settings, use_soxr)
        if log_callback:
            log_callback("be_encoding_soxr" if use_soxr else "be_encoding")
        proc = _run(cmd)
        if proc.returncode == 0 and mp3_out.exists() and mp3_out.stat().st_size > 0:
            return
        failures.append(f"$ {' '.join(cmd)}\nexit={proc.returncode}\nSTDERR:\n{proc.stderr}")

    raise ConvertError("err_convert", "\n---\n".join(failures))


def render_midi_to_mp3(
    fluidsynth: Path,
    ffmpeg: Path,
    soundfont: Path,
    midi: Path,
    mp3_out: Path,
    synth_settings: SynthSettings,
    mp3_settings: Mp3Settings,
    tmp_wav: Path,
    log_callback=None,
) -> None:
    render_wav(fluidsynth, soundfont, midi, tmp_wav, synth_settings, log_callback)
    convert_wav_to_mp3(ffmpeg, tmp_wav, mp3_out, mp3_settings, log_callback)
