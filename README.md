# MIDI Studio

<img src="midi-studio.svg" width="96" align="right" alt="MIDI Studio logo">

**English** | [Italiano](README.it.md)

MIDI Studio is a MIDI player and MIDI-to-MP3 converter **for Linux**, with a dark VLC-style
interface (PySide6). Sound is synthesized with [FluidSynth](https://www.fluidsynth.org/) and
encoded to MP3 with [FFmpeg](https://ffmpeg.org/) (LAME). The interface is bilingual
(English / Italian): it follows your system language and can be switched from the toolbar.

## Features
- Playlist with `.mid`, `.midi` and `.kar` files (open files or a whole folder)
- Playback with seek bar, volume and previous / next; audio output device selectable
- Full control of the synthesizer: SoundFont, interpolation (up to 7th order / sinc), sample rate,
  gain, polyphony, reverb, chorus, MIDI bank select mode, and quick presets (e.g. realistic piano)
- High-quality MP3 export: VBR or CBR, sample rate, soxr resampling, EBU R128 loudness normalization
- Batch conversion of several files, with confirmation before overwriting existing files
- All the heavy work runs in background threads: the interface never freezes

## Installation
System packages (Debian / Ubuntu / Kubuntu):

```bash
sudo apt install fluidsynth ffmpeg fluid-soundfont-gm libxcb-cursor0 libqt6svg6
```

`fluid-soundfont-gm` provides a General MIDI SoundFont; any `.sf2` / `.sf3` file works
(you can also set the `MIDI_SOUNDFONT` environment variable to a SoundFont path).

PySide6 - pick one:

```bash
sudo apt install python3-pyside6.qtwidgets        # from the repositories, if available
# or, in a virtual environment:
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```

## Usage
```bash
git clone https://github.com/MrGodLink/midi-studio.git
cd midi-studio
python3 main.py
```

## Project layout
| File | Purpose |
|------|---------|
| `main.py` | Graphical interface |
| `synth_backend.py` | Audio engine (FluidSynth + FFmpeg, no Python dependencies) |
| `i18n.py` | English / Italian strings |
| `midi-studio.svg` | Logo and window icon |

## Credits
Created by **Raffaele Catapano** - [github.com/MrGodLink](https://github.com/MrGodLink)

If you reuse, modify or redistribute this project, please keep the copyright notice and
credit the original author, as required by the MIT License.

### Other projects by the author
- [RcFux](https://github.com/MrGodLink/RuFux) - graphical utility (PySide6) to create bootable USB drives on Linux.
- [CISO-Converter](https://github.com/MrGodLink/CISO-Converter) - desktop tool (PySide6) to convert ISO to CSO and CSO to ISO, the compressed disc image format used by PSP and its emulators.

## License
The source code is released under the MIT License - see [LICENSE](LICENSE).

MIDI Studio depends on [PySide6](https://doc.qt.io/qtforpython/), licensed under the LGPLv3 (or a Qt commercial license). It is installed separately (via `pip` or your distribution). If you distribute a bundled executable (for example built with PyInstaller), you must also comply with the LGPL terms for PySide6 and Qt.
FluidSynth (LGPL) and FFmpeg (LGPL/GPL, depending on the build) are separate programs called through the command line and are not included in this repository. SoundFont files have their own licenses.
