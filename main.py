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
"""MIDI Studio - VLC-style MIDI player (dark theme, blue accents) for Linux, with
high-quality MP3 conversion based on FluidSynth + FFmpeg.

Run:  python3 main.py

Python dependencies:  PySide6  (pip install -r requirements.txt)
External tools:  fluidsynth, ffmpeg  (in the system PATH)
A GM SoundFont (.sf2 / .sf3) is also needed, e.g. FluidR3_GM.sf2.
The interface is bilingual (English / Italian), see i18n.py.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QLocale, QSize, Qt, QThread, QUrl, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtMultimedia import QAudioDevice, QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu, QMessageBox,
    QProgressBar, QPushButton, QRadioButton, QScrollArea, QSizePolicy, QSlider,
    QSpinBox, QStatusBar, QTabWidget, QToolBar, QVBoxLayout, QWidget,
)

import synth_backend as sb
from i18n import LANGUAGES, get_lang, set_lang, tr

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "midi-studio.svg")
APP_NAME = "MIDI Studio"
AUTHOR = "Raffaele Catapano"
__version__ = "1.0"


# ==========================================================================
# Dark theme, VLC style with blue accents
# ==========================================================================

DARK_QSS = """
QWidget {
    background-color: #14161b;
    color: #e6e9ef;
    font-family: "Noto Sans", "Ubuntu", "Cantarell", "DejaVu Sans", sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog { background-color: #14161b; }

QToolBar {
    background-color: #1a1d24;
    border: none;
    padding: 6px;
    spacing: 8px;
}

QListWidget {
    background-color: #1a1d24;
    border: 1px solid #262a33;
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 4px;
    margin: 1px 0px;
}
QListWidget::item:selected {
    background-color: #2f8ce0;
    color: #ffffff;
}
QListWidget::item:hover:!selected {
    background-color: #232733;
}

QLabel#TrackTitle {
    font-size: 15px;
    font-weight: 600;
    color: #ffffff;
}
QLabel#TimeLabel {
    color: #9aa4b2;
    font-size: 12px;
}
QLabel#SectionTitle {
    color: #6fb2ef;
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
}
QLabel#Hint { color: #767f8c; font-size: 11px; }
QLabel#Warn { color: #f0b429; font-size: 12px; }

/* --- Slider di ricerca / volume, stile VLC --- */
QSlider::groove:horizontal {
    height: 6px;
    background: #262a33;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #2f8ce0;
    border-radius: 3px;
}
QSlider::add-page:horizontal {
    background: #262a33;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #2f8ce0;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #dceaff;
}

/* --- Pulsanti generici --- */
QPushButton {
    background-color: #232733;
    color: #e6e9ef;
    border: 1px solid #2c3140;
    border-radius: 6px;
    padding: 7px 14px;
}
QPushButton:hover { background-color: #2b3040; border-color: #3a4258; }
QPushButton:pressed { background-color: #1d2029; }
QPushButton:disabled { color: #565d6b; background-color: #1c1f26; border-color: #232733; }

QPushButton#Primary {
    background-color: #2f8ce0;
    border: 1px solid #2f8ce0;
    color: #ffffff;
    font-weight: 600;
}
QPushButton#Primary:hover { background-color: #4a9de8; }
QPushButton#Primary:pressed { background-color: #266fb3; }

/* --- Pulsanti trasporto tondi stile VLC --- */
QPushButton#Transport {
    background-color: #232733;
    border: 1px solid #2c3140;
    border-radius: 21px;
    min-width: 42px; max-width: 42px;
    min-height: 42px; max-height: 42px;
    font-size: 16px;
    padding: 0px;
}
QPushButton#Transport:hover { background-color: #2b3040; }

QPushButton#PlayButton {
    background-color: #2f8ce0;
    border: 1px solid #2f8ce0;
    border-radius: 27px;
    min-width: 54px; max-width: 54px;
    min-height: 54px; max-height: 54px;
    font-size: 20px;
    color: #ffffff;
    padding: 0px;
}
QPushButton#PlayButton:hover { background-color: #4a9de8; }
QPushButton#PlayButton:pressed { background-color: #266fb3; }

QGroupBox {
    border: 1px solid #262a33;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: 600;
    color: #6fb2ef;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QTabWidget::pane { border: 1px solid #262a33; border-radius: 8px; top: -1px; }
QTabBar::tab {
    background: #1a1d24;
    color: #9aa4b2;
    padding: 8px 16px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}
QTabBar::tab:selected { background: #232733; color: #ffffff; border-bottom: 2px solid #2f8ce0; }
QTabBar::tab:hover:!selected { background: #202430; }

QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
    background-color: #1c1f26;
    border: 1px solid #2c3140;
    border-radius: 5px;
    padding: 5px 8px;
    selection-background-color: #2f8ce0;
}
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover { border-color: #3a4258; }
QComboBox::drop-down { border: none; width: 22px; }
QComboBox QAbstractItemView {
    background-color: #1c1f26;
    border: 1px solid #2c3140;
    selection-background-color: #2f8ce0;
    outline: none;
}

QCheckBox::indicator, QRadioButton::indicator {
    width: 16px; height: 16px;
}
QCheckBox::indicator:unchecked, QRadioButton::indicator:unchecked {
    border: 1px solid #3a4258; background: #1c1f26; border-radius: 3px;
}
QRadioButton::indicator:unchecked { border-radius: 8px; }
QCheckBox::indicator:checked {
    border: 1px solid #2f8ce0; background: #2f8ce0; border-radius: 3px;
}
QRadioButton::indicator:checked {
    border: 1px solid #2f8ce0; background: #2f8ce0; border-radius: 8px;
}

QStatusBar { background-color: #1a1d24; color: #9aa4b2; }
QProgressBar {
    background-color: #1c1f26;
    border: 1px solid #2c3140;
    border-radius: 5px;
    text-align: center;
    color: #e6e9ef;
    height: 14px;
}
QProgressBar::chunk { background-color: #2f8ce0; border-radius: 5px; }

QMenu { background-color: #1c1f26; border: 1px solid #2c3140; }
QMenu::item:selected { background-color: #2f8ce0; }

QScrollBar:vertical { background: #14161b; width: 10px; }
QScrollBar::handle:vertical { background: #2c3140; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: #3a4258; }
QScrollBar:horizontal { background: #14161b; height: 10px; }
QScrollBar::handle:horizontal { background: #2c3140; border-radius: 5px; min-width: 24px; }
"""



def format_time(ms: int) -> str:
    if ms < 0:
        ms = 0
    total_seconds = ms // 1000
    m, s = divmod(total_seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:d}:{s:02d}"


# ==========================================================================
# Worker threads (WAV rendering / MP3 conversion) - they never block the GUI
# ==========================================================================

def _error_parts(exc: Exception) -> Tuple[str, str]:
    """(message key, technical detail) of an exception raised by the backend."""
    if isinstance(exc, sb.BackendError):
        return exc.key, exc.detail
    return "err_unexpected", str(exc)


class RenderThread(QThread):
    status = Signal(str, dict)      # message key, parameters
    finished_ok = Signal(str)       # WAV path
    failed = Signal(str, str)       # message key, detail

    def __init__(self, fluidsynth: Path, soundfont: Path, midi: Path,
                 wav_out: Path, settings: sb.SynthSettings):
        super().__init__()
        self.fluidsynth = fluidsynth
        self.soundfont = soundfont
        self.midi = midi
        self.wav_out = wav_out
        self.settings = settings

    def run(self):
        try:
            sb.render_wav(
                self.fluidsynth, self.soundfont, self.midi, self.wav_out,
                self.settings, log_callback=lambda key, **p: self.status.emit(key, p),
            )
            self.finished_ok.emit(str(self.wav_out))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(*_error_parts(exc))


class ConvertThread(QThread):
    status = Signal(str, dict)           # message key, parameters
    file_done = Signal(str, str)         # midi_name, mp3_path
    file_failed = Signal(str, str, str)  # midi_name, message key, detail
    all_done = Signal()

    def __init__(self, fluidsynth: Path, ffmpeg: Path, soundfont: Path,
                 jobs: List[Tuple[Path, Path]], synth_settings: sb.SynthSettings,
                 mp3_settings: sb.Mp3Settings, tmp_dir: Path):
        super().__init__()
        self.fluidsynth = fluidsynth
        self.ffmpeg = ffmpeg
        self.soundfont = soundfont
        self.jobs = jobs
        self.synth_settings = synth_settings
        self.mp3_settings = mp3_settings
        self.tmp_dir = tmp_dir

    def run(self):
        for midi_path, mp3_path in self.jobs:
            wav_tmp = self.tmp_dir / f"_convert_{midi_path.stem}.wav"
            try:
                self.status.emit("rendering", {"name": midi_path.name})
                m3 = replace(self.mp3_settings, title_tag=midi_path.stem)
                sb.render_midi_to_mp3(
                    self.fluidsynth, self.ffmpeg, self.soundfont, midi_path,
                    mp3_path, self.synth_settings, m3, wav_tmp,
                    log_callback=lambda key, **p: self.status.emit(key, p),
                )
                self.file_done.emit(midi_path.name, str(mp3_path))
            except Exception as exc:  # noqa: BLE001
                self.file_failed.emit(midi_path.name, *_error_parts(exc))
            finally:
                if wav_tmp.exists():
                    try:
                        wav_tmp.unlink()
                    except OSError:
                        pass
        self.all_done.emit()


# ==========================================================================
# Settings dialog (Synthesizer + Playback)
# ==========================================================================

class SettingsDialog(QDialog):
    def __init__(self, parent, synth_settings: sb.SynthSettings,
                 extra_sf_dirs: List[Path], audio_devices: List[QAudioDevice],
                 current_device_id: Optional[bytes]):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_settings"))
        self.settings = synth_settings.clone()
        self.extra_sf_dirs = list(extra_sf_dirs)
        self.audio_devices = audio_devices
        self.selected_device_id = current_device_id

        tabs = QTabWidget()
        tabs.addTab(self._build_synth_tab(), tr("tab_synth"))
        tabs.addTab(self._build_playback_tab(), tr("tab_playback"))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("btn_ok"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("btn_cancel"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        layout.addWidget(buttons)

        # Width from the content (labels are longer in some languages), so that
        # no horizontal scrollbar appears
        self.resize(max(560, self._synth_inner.sizeHint().width() + 60), 620)

    # ---------------- Synthesizer tab ----------------
    def _build_synth_tab(self) -> QWidget:
        w = QWidget()
        outer = QVBoxLayout(w)

        # SoundFont
        sf_box = QGroupBox(tr("grp_soundfont"))
        sf_layout = QVBoxLayout(sf_box)
        row = QHBoxLayout()
        self.sf_combo = QComboBox()
        self._refresh_soundfont_list()
        row.addWidget(self.sf_combo, 1)
        browse_btn = QPushButton(tr("btn_browse"))
        browse_btn.clicked.connect(self._browse_soundfont)
        row.addWidget(browse_btn)
        rescan_btn = QPushButton(tr("btn_detect"))
        rescan_btn.clicked.connect(self._refresh_soundfont_list)
        row.addWidget(rescan_btn)
        sf_layout.addLayout(row)
        hint = QLabel(tr("sf_hint"))
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        sf_layout.addWidget(hint)
        outer.addWidget(sf_box)

        # Quick presets
        preset_box = QGroupBox(tr("grp_presets"))
        preset_layout = QHBoxLayout(preset_box)
        btn_default = QPushButton(tr("preset_default"))
        btn_piano = QPushButton(tr("preset_piano"))
        btn_low = QPushButton(tr("preset_low"))
        btn_default.clicked.connect(lambda: self._apply_preset(sb.preset_default))
        btn_piano.clicked.connect(lambda: self._apply_preset(sb.preset_realistic_piano))
        btn_low.clicked.connect(lambda: self._apply_preset(sb.preset_low_resources))
        preset_layout.addWidget(btn_default)
        preset_layout.addWidget(btn_piano)
        preset_layout.addWidget(btn_low)
        outer.addWidget(preset_box)

        # Synthesis quality
        quality_box = QGroupBox(tr("grp_quality"))
        form = QFormLayout(quality_box)

        self.interp_combo = QComboBox()
        for label in sb.INTERPOLATION_METHODS:
            self.interp_combo.addItem(tr(label))
        self._set_combo_by_value(self.interp_combo, sb.INTERPOLATION_METHODS, self.settings.interpolation)
        form.addRow(tr("lbl_interp"), self.interp_combo)

        self.samplerate_combo = QComboBox()
        self.samplerate_combo.addItems(["22050", "44100", "48000", "88200", "96000"])
        self.samplerate_combo.setCurrentText(str(int(self.settings.sample_rate)))
        form.addRow(tr("lbl_synth_sr"), self.samplerate_combo)

        self.audio_format_combo = QComboBox()
        self.audio_format_combo.addItems(sb.AUDIO_FILE_FORMATS)
        self.audio_format_combo.setCurrentText(self.settings.audio_file_format)
        form.addRow(tr("lbl_wav_fmt"), self.audio_format_combo)

        self.gain_spin = QDoubleSpinBox()
        self.gain_spin.setRange(0.0, 10.0)
        self.gain_spin.setSingleStep(0.05)
        self.gain_spin.setValue(self.settings.gain)
        form.addRow(tr("lbl_gain"), self.gain_spin)

        self.polyphony_spin = QSpinBox()
        self.polyphony_spin.setRange(1, 65535)
        self.polyphony_spin.setValue(self.settings.polyphony)
        form.addRow(tr("lbl_poly"), self.polyphony_spin)

        self.cpu_spin = QSpinBox()
        self.cpu_spin.setRange(1, 32)
        self.cpu_spin.setValue(self.settings.cpu_cores)
        form.addRow(tr("lbl_cores"), self.cpu_spin)

        self.bank_combo = QComboBox()
        self.bank_combo.addItems(sb.MIDI_BANK_SELECT_MODES)
        self.bank_combo.setCurrentText(self.settings.midi_bank_select)
        form.addRow(tr("lbl_bank"), self.bank_combo)

        outer.addWidget(quality_box)

        # Reverb
        self.reverb_box = QGroupBox(tr("grp_reverb"))
        self.reverb_box.setCheckable(True)
        self.reverb_box.setChecked(self.settings.reverb.active)
        rlay = QFormLayout(self.reverb_box)
        self.rev_room = self._make_slider_row(rlay, tr("rev_room"), 0, 100,
                                               int(self.settings.reverb.room_size * 100))
        self.rev_damp = self._make_slider_row(rlay, tr("rev_damp"), 0, 100,
                                               int(self.settings.reverb.damping * 100))
        self.rev_width = self._make_slider_row(rlay, tr("rev_width"), 0, 100,
                                                int(min(self.settings.reverb.width, 1.0) * 100))
        self.rev_level = self._make_slider_row(rlay, tr("rev_level"), 0, 100,
                                                int(self.settings.reverb.level * 100))
        outer.addWidget(self.reverb_box)

        # Chorus
        self.chorus_box = QGroupBox(tr("grp_chorus"))
        self.chorus_box.setCheckable(True)
        self.chorus_box.setChecked(self.settings.chorus.active)
        clay = QFormLayout(self.chorus_box)
        self.cho_nr = QSpinBox()
        self.cho_nr.setRange(0, 99)
        self.cho_nr.setValue(self.settings.chorus.voice_count)
        clay.addRow(tr("cho_voices"), self.cho_nr)
        self.cho_level = self._make_slider_row(clay, tr("cho_level"), 0, 1000,
                                                int(self.settings.chorus.level * 100), div=100)
        self.cho_speed = self._make_slider_row(clay, tr("cho_speed"), 10, 500,
                                                int(self.settings.chorus.speed_hz * 100), div=100)
        self.cho_depth = self._make_slider_row(clay, tr("cho_depth"), 0, 256,
                                                int(self.settings.chorus.depth_ms), div=1)
        self.cho_type = QComboBox()
        self.cho_type.addItems([tr(k) for k in sb.CHORUS_TYPES])
        self._set_combo_by_value(self.cho_type, sb.CHORUS_TYPES, self.settings.chorus.mod_type)
        clay.addRow(tr("cho_wave"), self.cho_type)
        outer.addWidget(self.chorus_box)

        outer.addStretch(1)
        self._synth_inner = w
        return self._wrap_scroll(w)

    def _wrap_scroll(self, inner: QWidget) -> QWidget:
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(inner)
        area.setFrameShape(QScrollArea.Shape.NoFrame)
        area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return area

    def _make_slider_row(self, layout: QFormLayout, label: str, lo: int, hi: int,
                          value: int, div: int = 100):
        row = QHBoxLayout()
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(value)
        value_lbl = QLabel(f"{value / div:.2f}")
        value_lbl.setFixedWidth(48)
        slider.valueChanged.connect(lambda v: value_lbl.setText(f"{v / div:.2f}"))
        row.addWidget(slider, 1)
        row.addWidget(value_lbl)
        holder = QWidget()
        holder.setLayout(row)
        layout.addRow(label + ":", holder)
        return slider

    def _set_combo_by_value(self, combo: QComboBox, mapping: Dict[str, int], value: int):
        for i, (k, v) in enumerate(mapping.items()):
            if v == value:
                combo.setCurrentIndex(i)
                return

    def _apply_preset(self, preset_fn):
        self.settings = preset_fn(self.settings)
        self._set_combo_by_value(self.interp_combo, sb.INTERPOLATION_METHODS, self.settings.interpolation)
        self.samplerate_combo.setCurrentText(str(int(self.settings.sample_rate)))
        self.audio_format_combo.setCurrentText(self.settings.audio_file_format)
        self.gain_spin.setValue(self.settings.gain)
        self.polyphony_spin.setValue(self.settings.polyphony)
        self.reverb_box.setChecked(self.settings.reverb.active)
        self.rev_room.setValue(int(self.settings.reverb.room_size * 100))
        self.rev_damp.setValue(int(self.settings.reverb.damping * 100))
        self.rev_width.setValue(int(min(self.settings.reverb.width, 1.0) * 100))
        self.rev_level.setValue(int(self.settings.reverb.level * 100))
        self.chorus_box.setChecked(self.settings.chorus.active)
        self.cho_nr.setValue(self.settings.chorus.voice_count)
        self.cho_level.setValue(int(self.settings.chorus.level * 100))
        self.cho_speed.setValue(int(self.settings.chorus.speed_hz * 100))
        self.cho_depth.setValue(int(self.settings.chorus.depth_ms))

    def _refresh_soundfont_list(self):
        current = self.sf_combo.currentData() if self.sf_combo.count() else None
        self.sf_combo.clear()
        fonts = sb.list_soundfonts(self.extra_sf_dirs)
        if self.settings.soundfont:
            cur_path = Path(self.settings.soundfont)
            if cur_path.is_file() and cur_path not in fonts:
                fonts.insert(0, cur_path)
        for f in fonts:
            self.sf_combo.addItem(f.name, str(f))
        if not fonts:
            self.sf_combo.addItem(tr("no_sf_found"), "")
        # re-select the previous choice (kept when "Detect" is pressed), else the active one
        wanted = current or self.settings.soundfont
        if wanted:
            idx = self.sf_combo.findData(wanted)
            if idx >= 0:
                self.sf_combo.setCurrentIndex(idx)

    def _browse_soundfont(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("dlg_pick_sf"), str(Path.home()), "SoundFont (*.sf2 *.sf3 *.SF2 *.SF3)"
        )
        if path:
            p = Path(path)
            if p.parent not in self.extra_sf_dirs:
                self.extra_sf_dirs.append(p.parent)
            self.settings.soundfont = str(p)
            self._refresh_soundfont_list()

    # ---------------- Playback tab ----------------
    def _build_playback_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)

        box = QGroupBox(tr("grp_audio_out"))
        form = QFormLayout(box)
        self.device_combo = QComboBox()
        self.device_combo.addItem(tr("dev_default"), None)
        for dev in self.audio_devices:
            self.device_combo.addItem(dev.description(), dev.id())
        if self.selected_device_id is not None:
            idx = self.device_combo.findData(self.selected_device_id)
            if idx >= 0:
                self.device_combo.setCurrentIndex(idx)
        form.addRow(tr("lbl_audio_card"), self.device_combo)
        layout.addWidget(box)

        note = QLabel(tr("playback_note"))
        note.setObjectName("Hint")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch(1)
        return w

    # ---------------- Collect result ----------------
    def result_settings(self) -> sb.SynthSettings:
        s = self.settings
        s.soundfont = self.sf_combo.currentData() or None
        s.interpolation = list(sb.INTERPOLATION_METHODS.values())[self.interp_combo.currentIndex()]
        s.sample_rate = float(self.samplerate_combo.currentText())
        s.audio_file_format = self.audio_format_combo.currentText()
        s.gain = self.gain_spin.value()
        s.polyphony = self.polyphony_spin.value()
        s.cpu_cores = self.cpu_spin.value()
        s.midi_bank_select = self.bank_combo.currentText()
        s.reverb.active = self.reverb_box.isChecked()
        s.reverb.room_size = self.rev_room.value() / 100
        s.reverb.damping = self.rev_damp.value() / 100
        s.reverb.width = self.rev_width.value() / 100
        s.reverb.level = self.rev_level.value() / 100
        s.chorus.active = self.chorus_box.isChecked()
        s.chorus.voice_count = self.cho_nr.value()
        s.chorus.level = self.cho_level.value() / 100
        s.chorus.speed_hz = self.cho_speed.value() / 100
        s.chorus.depth_ms = self.cho_depth.value()
        s.chorus.mod_type = list(sb.CHORUS_TYPES.values())[self.cho_type.currentIndex()]
        return s

    def result_device_id(self) -> Optional[bytes]:
        return self.device_combo.currentData()

    def result_extra_dirs(self) -> List[Path]:
        return self.extra_sf_dirs


# ==========================================================================
# MP3 conversion dialog
# ==========================================================================

class ConvertDialog(QDialog):
    def __init__(self, parent, midi_files: List[Path], default_out_dir: Path,
                 mp3_settings: sb.Mp3Settings):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_convert"))
        self._running = False
        self.midi_files = midi_files
        self.mp3_settings = mp3_settings
        self.output_dir = default_out_dir
        self.single_output_file: Optional[Path] = None

        layout = QVBoxLayout(self)

        info = QLabel(
            tr("files_one") if len(midi_files) == 1 else tr("files_n", n=len(midi_files))
        )
        info.setObjectName("SectionTitle")
        layout.addWidget(info)

        # Destination
        dest_box = QGroupBox(tr("grp_dest"))
        dest_layout = QVBoxLayout(dest_box)
        row = QHBoxLayout()
        self.dest_edit = QLineEdit()
        if len(midi_files) == 1:
            self.single_output_file = default_out_dir / f"{midi_files[0].stem}.mp3"
            self.dest_edit.setText(str(self.single_output_file))
        else:
            self.dest_edit.setText(str(default_out_dir))
        row.addWidget(self.dest_edit, 1)
        browse_btn = QPushButton(tr("btn_browse"))
        browse_btn.clicked.connect(self._browse_dest)
        row.addWidget(browse_btn)
        dest_layout.addLayout(row)
        layout.addWidget(dest_box)

        # MP3 quality
        q_box = QGroupBox(tr("grp_mp3"))
        q_layout = QVBoxLayout(q_box)

        mode_row = QHBoxLayout()
        self.rb_vbr = QRadioButton(tr("rb_vbr"))
        self.rb_cbr = QRadioButton(tr("rb_cbr"))
        self.rb_vbr.setChecked(mp3_settings.mode != "cbr")
        self.rb_cbr.setChecked(mp3_settings.mode == "cbr")
        group = QButtonGroup(self)
        group.addButton(self.rb_vbr)
        group.addButton(self.rb_cbr)
        mode_row.addWidget(self.rb_vbr)
        mode_row.addWidget(self.rb_cbr)
        q_layout.addLayout(mode_row)

        form = QFormLayout()
        self.vbr_spin = QSpinBox()
        self.vbr_spin.setRange(0, 9)
        self.vbr_spin.setValue(mp3_settings.vbr_quality)
        self.vbr_spin.setToolTip(tr("vbr_tip"))
        form.addRow(tr("lbl_vbr"), self.vbr_spin)

        self.cbr_combo = QComboBox()
        self.cbr_combo.addItems(["128k", "192k", "256k", "320k"])
        self.cbr_combo.setCurrentText(mp3_settings.cbr_bitrate)
        form.addRow(tr("lbl_cbr"), self.cbr_combo)

        self.sr_combo = QComboBox()
        self.sr_combo.addItems(["22050", "32000", "44100", "48000"])
        self.sr_combo.setCurrentText(str(mp3_settings.sample_rate))
        form.addRow(tr("lbl_mp3_sr"), self.sr_combo)
        q_layout.addLayout(form)

        self.chk_soxr = QCheckBox(tr("chk_soxr"))
        self.chk_soxr.setChecked(mp3_settings.high_quality_resample)
        q_layout.addWidget(self.chk_soxr)

        self.chk_norm = QCheckBox(tr("chk_norm"))
        self.chk_norm.setChecked(mp3_settings.normalize_loudness)
        q_layout.addWidget(self.chk_norm)

        layout.addWidget(q_box)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        self.status_lbl = QLabel("")
        self.status_lbl.setObjectName("Hint")
        self.status_lbl.setWordWrap(True)
        layout.addWidget(self.status_lbl)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("btn_convert"))
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("btn_cancel"))
        self.buttons.accepted.connect(self._on_convert_clicked)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self._convert_thread: Optional[ConvertThread] = None
        self._on_convert_callback = None
        self.resize(max(480, self.sizeHint().width() + 20), 460)

    def _browse_dest(self):
        if len(self.midi_files) == 1:
            path, _ = QFileDialog.getSaveFileName(
                self, tr("dlg_save_mp3"), self.dest_edit.text(), "MP3 (*.mp3)"
            )
            if path:
                self.dest_edit.setText(path)
        else:
            path = QFileDialog.getExistingDirectory(self, tr("dlg_dest_dir"), self.dest_edit.text())
            if path:
                self.dest_edit.setText(path)

    def collected_mp3_settings(self) -> sb.Mp3Settings:
        m = self.mp3_settings
        m.mode = "cbr" if self.rb_cbr.isChecked() else "vbr"
        m.vbr_quality = self.vbr_spin.value()
        m.cbr_bitrate = self.cbr_combo.currentText()
        m.sample_rate = int(self.sr_combo.currentText())
        m.high_quality_resample = self.chk_soxr.isChecked()
        m.normalize_loudness = self.chk_norm.isChecked()
        return m

    def jobs(self) -> List[Tuple[Path, Path]]:
        dest_text = self.dest_edit.text().strip()
        result = []
        if len(self.midi_files) == 1:
            out = Path(dest_text) if dest_text else self.single_output_file
            if out.suffix.lower() != ".mp3":
                out = out.with_suffix(".mp3")
            result.append((self.midi_files[0], out))
        else:
            out_dir = Path(dest_text)
            for midi in self.midi_files:
                result.append((midi, out_dir / f"{midi.stem}.mp3"))
        return result

    def set_runner(self, callback):
        """callback(jobs, mp3_settings, dialog) must start the conversion and
        report back through dialog.mark_progress / dialog.mark_finished."""
        self._on_convert_callback = callback

    def reject(self):
        # Esc / window close must not destroy the dialog while the worker thread
        # is still reporting to it
        if self._running:
            return
        super().reject()

    def _on_convert_clicked(self):
        existing = [out for _, out in self.jobs() if out.exists()]
        if existing:
            r = QMessageBox.question(
                self, tr("overwrite_title"), tr("overwrite_text", n=len(existing)),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if r != QMessageBox.StandardButton.Yes:
                return
        self._running = True
        self.buttons.setEnabled(False)
        self.progress.setVisible(True)
        self.status_lbl.setText(tr("starting_conv"))
        if self._on_convert_callback:
            self._on_convert_callback(self.jobs(), self.collected_mp3_settings(), self)

    def mark_progress(self, key: str, params: Optional[dict] = None):
        self.status_lbl.setText(tr(key, **(params or {})))

    def mark_finished(self, ok_count: int, err_count: int):
        self._running = False
        self.progress.setVisible(False)
        self.buttons.setEnabled(True)
        if err_count:
            self.status_lbl.setText(tr("conv_finished_err", ok=ok_count, err=err_count))
        else:
            self.status_lbl.setText(tr("conv_finished", ok=ok_count))
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("btn_close"))
        try:
            self.buttons.accepted.disconnect()
        except TypeError:
            pass
        self.buttons.accepted.connect(self.accept)



# ==========================================================================
# Main window
# ==========================================================================

class MainWindow(QMainWindow):
    WAV_CACHE_MAX = 4   # rendered WAVs kept in the temporary folder (they are big)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} * Author : {AUTHOR}")
        self.resize(880, 620)

        self.synth_settings = sb.SynthSettings()
        self.mp3_settings = sb.Mp3Settings()
        self.extra_sf_dirs: List[Path] = []
        self.current_device_id: Optional[bytes] = None

        self.tmp_dir = Path(tempfile.mkdtemp(prefix="midistudio_"))
        self.wav_cache: Dict[Tuple[str, tuple], Path] = {}   # insertion order = LRU order
        self.playlist_paths: List[Path] = []
        self.current_index: int = -1
        self._seeking = False
        self._render_thread: Optional[RenderThread] = None
        self._pending_play_after_render = False
        self._last_status = None   # (key, timeout, params) of the last status message

        # Default SoundFont, if present
        fonts = sb.list_soundfonts()
        if fonts:
            self.synth_settings.soundfont = str(fonts[0])

        # --- Media player ---
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0.8)
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.playbackStateChanged.connect(self._on_playback_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
        self.player.errorOccurred.connect(self._on_player_error)

        self._build_ui()
        self.retranslate()
        self._show_status("status_ready")
        self._check_tools()

    # ---------------------------------------------------------------- UI --
    def _build_ui(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        self.act_open = QAction(self)
        self.act_open.triggered.connect(self._open_files)
        toolbar.addAction(self.act_open)

        self.act_open_folder = QAction(self)
        self.act_open_folder.triggered.connect(self._open_folder)
        toolbar.addAction(self.act_open_folder)

        toolbar.addSeparator()

        self.act_convert = QAction(self)
        self.act_convert.triggered.connect(self._open_convert_dialog)
        toolbar.addAction(self.act_convert)

        toolbar.addSeparator()

        self.act_settings = QAction(self)
        self.act_settings.triggered.connect(self._open_settings_dialog)
        toolbar.addAction(self.act_settings)

        # Language selector on the right side of the toolbar
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        spacer.setStyleSheet("background: transparent;")
        toolbar.addWidget(spacer)
        self.lang_label = QLabel()
        self.lang_label.setStyleSheet("background: transparent;")
        toolbar.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        for code, name in LANGUAGES:
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(self.lang_combo.findData(get_lang()))
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        toolbar.addWidget(self.lang_combo)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(10)

        # Playlist
        self.list_label = QLabel()
        self.list_label.setObjectName("SectionTitle")
        root.addWidget(self.list_label)

        self.playlist_widget = QListWidget()
        self.playlist_widget.itemDoubleClicked.connect(self._on_playlist_double_click)
        self.playlist_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_widget.customContextMenuRequested.connect(self._show_playlist_menu)
        self.playlist_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        root.addWidget(self.playlist_widget, 1)

        # Current track title
        self.track_title_lbl = QLabel()
        self.track_title_lbl.setObjectName("TrackTitle")
        root.addWidget(self.track_title_lbl)

        # Seek bar
        seek_row = QHBoxLayout()
        self.elapsed_lbl = QLabel("0:00")
        self.elapsed_lbl.setObjectName("TimeLabel")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self.seek_slider.sliderReleased.connect(self._on_seek_released)
        self.total_lbl = QLabel("0:00")
        self.total_lbl.setObjectName("TimeLabel")
        seek_row.addWidget(self.elapsed_lbl)
        seek_row.addWidget(self.seek_slider, 1)
        seek_row.addWidget(self.total_lbl)
        root.addLayout(seek_row)

        # Transport
        transport_row = QHBoxLayout()
        transport_row.setSpacing(10)

        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setObjectName("Transport")
        self.prev_btn.clicked.connect(self._play_previous)

        self.play_btn = QPushButton("▶")
        self.play_btn.setObjectName("PlayButton")
        self.play_btn.clicked.connect(self._toggle_play_pause)

        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setObjectName("Transport")
        self.stop_btn.clicked.connect(self._stop)

        self.next_btn = QPushButton("⏭")
        self.next_btn.setObjectName("Transport")
        self.next_btn.clicked.connect(self._play_next)

        transport_row.addStretch(1)
        transport_row.addWidget(self.prev_btn)
        transport_row.addWidget(self.play_btn)
        transport_row.addWidget(self.stop_btn)
        transport_row.addWidget(self.next_btn)
        transport_row.addStretch(1)

        vol_box = QHBoxLayout()
        vol_icon = QLabel("🔊")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        vol_box.addWidget(vol_icon)
        vol_box.addWidget(self.volume_slider)

        outer_transport = QHBoxLayout()
        outer_transport.addLayout(transport_row, 1)
        outer_transport.addLayout(vol_box)
        root.addLayout(outer_transport)

        self.setStatusBar(QStatusBar())
        self.render_progress = QProgressBar()
        self.render_progress.setRange(0, 0)
        self.render_progress.setVisible(False)
        self.render_progress.setFixedWidth(160)
        self.statusBar().addPermanentWidget(self.render_progress)

    # ---------------------------------------------------------- Language --
    def _on_language_changed(self):
        set_lang(self.lang_combo.currentData())
        self.retranslate()

    def retranslate(self):
        """(Re)apply every visible text of the main window in the current language."""
        self.act_open.setText(tr("act_open"))
        self.act_open_folder.setText(tr("act_open_folder"))
        self.act_convert.setText(tr("act_convert"))
        self.act_settings.setText(tr("act_settings"))
        self.lang_label.setText(tr("language"))
        self.list_label.setText(tr("playlist"))
        if self.current_index < 0:
            self.track_title_lbl.setText(tr("no_track"))
        if self._last_status and self.statusBar().currentMessage():
            key, timeout, params = self._last_status
            self._show_status(key, timeout, **params)

    def _show_status(self, key: str, timeout: int = 0, **params):
        """Show a translated status message (re-translated on language change)."""
        self._last_status = (key, timeout, params)
        self.statusBar().showMessage(tr(key, **params), timeout)

    # ------------------------------------------------------------ Tools --
    def _check_tools(self):
        tools = sb.tools_available()
        missing = [name for name, path in tools.items() if not path]
        if missing:
            QMessageBox.warning(
                self, tr("tools_missing_title"),
                tr("tools_missing_text", tools=", ".join(missing)),
            )
        if not self.synth_settings.soundfont:
            self._show_status("no_soundfont_status", 8000)

    # --------------------------------------------------------- Playlist --
    def _open_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr("dlg_open_midi"), str(Path.home()), tr("dlg_midi_filter")
        )
        for p in paths:
            self._add_to_playlist(Path(p))

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr("dlg_open_folder"), str(Path.home()))
        if not folder:
            return
        added = 0
        for f in sorted(Path(folder).iterdir()):
            if f.is_file() and sb.is_midi_file(f):
                self._add_to_playlist(f)
                added += 1
        self._show_status("folder_added", 4000, n=added)

    def _add_to_playlist(self, path: Path):
        if not path.is_file():
            return
        item = QListWidgetItem(path.stem)
        item.setData(Qt.ItemDataRole.UserRole, str(path))
        self.playlist_widget.addItem(item)
        self.playlist_paths.append(path)

    def _show_playlist_menu(self, pos):
        menu = QMenu(self)
        act_play = menu.addAction(tr("menu_play"))
        act_convert = menu.addAction(tr("act_convert"))
        act_remove = menu.addAction(tr("menu_remove"))
        chosen = menu.exec(self.playlist_widget.mapToGlobal(pos))
        if chosen == act_play:
            row = self.playlist_widget.currentRow()
            if row >= 0:
                self._play_index(row)
        elif chosen == act_convert:
            self._open_convert_dialog()
        elif chosen == act_remove:
            for item in self.playlist_widget.selectedItems():
                row = self.playlist_widget.row(item)
                self.playlist_widget.takeItem(row)
                del self.playlist_paths[row]
                # keep the "current track" pointer consistent with the shifted list
                if row < self.current_index:
                    self.current_index -= 1
                elif row == self.current_index:
                    self.current_index = -1

    def _on_playlist_double_click(self, item: QListWidgetItem):
        self._play_index(self.playlist_widget.row(item))

    # ---------------------------------------------------------- Playback --
    def _play_index(self, index: int):
        if index < 0 or index >= len(self.playlist_paths):
            return
        # A second rendering thread would replace the running one while it is
        # still active (Qt aborts when a running QThread is destroyed)
        if self._render_thread is not None and self._render_thread.isRunning():
            self._show_status("render_busy", 3000)
            return
        self.current_index = index
        self.playlist_widget.setCurrentRow(index)
        midi_path = self.playlist_paths[index]
        self.track_title_lbl.setText(midi_path.stem)
        self._pending_play_after_render = True
        self._render_and_load(midi_path)

    def _play_previous(self):
        if self.current_index > 0:
            self._play_index(self.current_index - 1)

    def _play_next(self):
        if self.current_index + 1 < len(self.playlist_paths):
            self._play_index(self.current_index + 1)

    def _render_and_load(self, midi_path: Path):
        if not self.synth_settings.soundfont:
            QMessageBox.warning(self, tr("no_soundfont_title"), tr("no_soundfont_text"))
            return
        try:
            fluidsynth = sb.find_tool("fluidsynth")
        except sb.ToolNotFoundError:
            QMessageBox.critical(self, tr("fluidsynth_missing_title"), tr("fluidsynth_missing_text"))
            return

        key = (str(midi_path), self.synth_settings.fingerprint())
        cached = self.wav_cache.get(key)
        if cached and cached.exists():
            self.wav_cache[key] = self.wav_cache.pop(key)   # mark as most recently used
            self._load_wav_and_play(cached)
            return

        wav_out = self.tmp_dir / f"play_{midi_path.stem}_{abs(hash(key))}.wav"
        self._set_busy(True, "rendering", name=midi_path.name)

        self._render_thread = RenderThread(
            fluidsynth, Path(self.synth_settings.soundfont), midi_path, wav_out,
            self.synth_settings.clone(),
        )
        self._render_thread.status.connect(lambda k, p: self._show_status(k, 0, **p))
        self._render_thread.finished_ok.connect(
            lambda wav: self._on_render_finished(key, Path(wav))
        )
        self._render_thread.failed.connect(self._on_render_failed)
        self._render_thread.start()

    def _cache_wav(self, key, wav_path: Path):
        """Remember a rendered WAV, deleting the oldest ones (a float WAV is ~20 MB/min)."""
        self.wav_cache.pop(key, None)
        self.wav_cache[key] = wav_path
        while len(self.wav_cache) > self.WAV_CACHE_MAX:
            old = self.wav_cache.pop(next(iter(self.wav_cache)))
            try:
                old.unlink()
            except OSError:
                pass

    def _on_render_finished(self, key, wav_path: Path):
        self._set_busy(False, "status_ready")
        self._cache_wav(key, wav_path)
        self._load_wav_and_play(wav_path)

    def _on_render_failed(self, key: str, detail: str):
        self._set_busy(False, "render_error_status")
        message = tr(key) + (f"\n\n{detail}" if detail else "")
        QMessageBox.critical(self, tr("render_error_title"), message)

    def _load_wav_and_play(self, wav_path: Path):
        self.player.setSource(QUrl.fromLocalFile(str(wav_path)))
        if self._pending_play_after_render:
            self.player.play()
            self._pending_play_after_render = False

    def _toggle_play_pause(self):
        state = self.player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.player.play()
        else:
            if self.current_index == -1 and self.playlist_paths:
                self._play_index(0)
            elif self.player.source().isValid():
                self.player.play()

    def _stop(self):
        self.player.stop()

    def _on_seek_released(self):
        self._seeking = False
        self.player.setPosition(self.seek_slider.value())

    def _on_position_changed(self, pos_ms: int):
        if not self._seeking:
            self.seek_slider.setValue(pos_ms)
        self.elapsed_lbl.setText(format_time(pos_ms))

    def _on_duration_changed(self, dur_ms: int):
        self.seek_slider.setRange(0, max(dur_ms, 0))
        self.total_lbl.setText(format_time(dur_ms))

    def _on_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_btn.setText("⏸")
        else:
            self.play_btn.setText("▶")

    def _on_media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._play_next()

    def _on_player_error(self, error, error_string: str):
        if error != QMediaPlayer.Error.NoError:
            self._show_status("playback_error", 6000, err=error_string)

    def _on_volume_changed(self, value: int):
        self.audio_output.setVolume(value / 100)

    def _set_busy(self, busy: bool, key: str, **params):
        self.render_progress.setVisible(busy)
        self._show_status(key, 0 if busy else 4000, **params)
        self.play_btn.setEnabled(not busy)

    # --------------------------------------------------------- Settings --
    def _open_settings_dialog(self):
        devices = QMediaDevices.audioOutputs()
        dlg = SettingsDialog(self, self.synth_settings, self.extra_sf_dirs,
                              devices, self.current_device_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.synth_settings = dlg.result_settings()
            self.extra_sf_dirs = dlg.result_extra_dirs()
            device_id = dlg.result_device_id()
            self.current_device_id = device_id
            if device_id is not None:
                for dev in devices:
                    if dev.id() == device_id:
                        self.audio_output.setDevice(dev)
                        break
            else:
                self.audio_output.setDevice(QMediaDevices.defaultAudioOutput())
            self._show_status("settings_updated", 3000)

    # --------------------------------------------------------- Convert --
    def _open_convert_dialog(self):
        selected = self.playlist_widget.selectedItems()
        if selected:
            midi_files = [Path(it.data(Qt.ItemDataRole.UserRole)) for it in selected]
        elif self.current_index >= 0:
            midi_files = [self.playlist_paths[self.current_index]]
        elif self.playlist_paths:
            midi_files = list(self.playlist_paths)
        else:
            paths, _ = QFileDialog.getOpenFileNames(
                self, tr("pick_midi_convert"), str(Path.home()), tr("dlg_midi_filter")
            )
            if not paths:
                return
            midi_files = [Path(p) for p in paths]

        if not self.synth_settings.soundfont:
            QMessageBox.warning(self, tr("no_soundfont_title"), tr("no_soundfont_text"))
            return

        default_dir = midi_files[0].parent
        dlg = ConvertDialog(self, midi_files, default_dir, self.mp3_settings)
        dlg.set_runner(self._run_conversion)
        dlg.exec()

    def _run_conversion(self, jobs: List[Tuple[Path, Path]], mp3_settings: sb.Mp3Settings,
                         dialog: ConvertDialog):
        try:
            fluidsynth = sb.find_tool("fluidsynth")
            ffmpeg = sb.find_tool("ffmpeg")
        except sb.ToolNotFoundError as exc:
            QMessageBox.critical(self, tr("tool_missing_title"), tr("tool_missing_text", tool=str(exc)))
            dialog.mark_finished(0, len(jobs))
            return

        self.mp3_settings = mp3_settings
        thread = ConvertThread(
            fluidsynth, ffmpeg, Path(self.synth_settings.soundfont), jobs,
            self.synth_settings.clone(), mp3_settings, self.tmp_dir,
        )
        self._ok_count = 0
        self._err_count = 0
        self._total_jobs = len(jobs)

        thread.status.connect(dialog.mark_progress)

        def on_done(name, path):
            self._ok_count += 1
            dialog.mark_progress("conv_done_file", {"name": name})

        def on_failed(name, key, detail):
            self._err_count += 1
            text = " ".join(f"{tr(key)} {detail}".split())
            dialog.mark_progress("conv_err_file", {"name": name, "err": text[:120]})

        def on_all_done():
            dialog.mark_finished(self._ok_count, self._err_count)

        thread.file_done.connect(on_done)
        thread.file_failed.connect(on_failed)
        thread.all_done.connect(on_all_done)
        self._convert_thread = thread
        thread.start()

    # ------------------------------------------------------------ Exit --
    def closeEvent(self, event):
        if self._render_thread is not None and self._render_thread.isRunning():
            QMessageBox.information(self, APP_NAME, tr("busy_quit"))
            event.ignore()
            return
        self.player.stop()
        try:
            shutil.rmtree(self.tmp_dir, ignore_errors=True)
        except Exception:
            pass
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(__version__)
    if os.path.isfile(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    app.setStyleSheet(DARK_QSS)
    set_lang("it" if QLocale.system().name().startswith("it") else "en")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
