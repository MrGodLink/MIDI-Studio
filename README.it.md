# MIDI Studio

<img src="midi-studio.svg" width="96" align="right" alt="Logo MIDI Studio">

[English](README.md) | **Italiano**

MIDI Studio è un lettore MIDI e convertitore MIDI-MP3 **per Linux**, con un'interfaccia scura
in stile VLC (PySide6). Il suono viene sintetizzato con [FluidSynth](https://www.fluidsynth.org/)
e codificato in MP3 con [FFmpeg](https://ffmpeg.org/) (LAME). L'interfaccia è bilingue
(inglese / italiano): segue la lingua del sistema e si cambia dalla barra degli strumenti.

## Funzioni
- Playlist con file `.mid`, `.midi` e `.kar` (apri file o un'intera cartella)
- Riproduzione con barra di avanzamento, volume e brano precedente / successivo; uscita audio selezionabile
- Controllo completo del sintetizzatore: SoundFont, interpolazione (fino al 7° ordine / sinc),
  frequenza di campionamento, gain, polifonia, riverbero, chorus, modalità Bank Select MIDI e
  preset rapidi (per esempio piano realistico)
- Esportazione MP3 di alta qualità: VBR o CBR, frequenza di campionamento, ricampionamento soxr,
  normalizzazione del volume EBU R128
- Conversione di più file insieme, con conferma prima di sovrascrivere i file esistenti
- Il lavoro pesante gira in thread separati: l'interfaccia non si blocca mai

## Installazione
Pacchetti di sistema (Debian / Ubuntu / Kubuntu):

```bash
sudo apt install fluidsynth ffmpeg fluid-soundfont-gm libxcb-cursor0 libqt6svg6
```

`fluid-soundfont-gm` fornisce un SoundFont General MIDI; va bene qualsiasi file `.sf2` / `.sf3`
(puoi anche impostare la variabile d'ambiente `MIDI_SOUNDFONT` con il percorso di un SoundFont).

PySide6 - scegli una opzione:

```bash
sudo apt install python3-pyside6.qtwidgets        # dai repository, se disponibile
# oppure, in un ambiente virtuale:
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
```

## Uso
```bash
git clone https://github.com/MrGodLink/midi-studio.git
cd midi-studio
python3 main.py
```

## Struttura del progetto
| File | Scopo |
|------|-------|
| `main.py` | Interfaccia grafica |
| `synth_backend.py` | Motore audio (FluidSynth + FFmpeg, nessuna dipendenza Python) |
| `i18n.py` | Testi in inglese / italiano |
| `midi-studio.svg` | Logo e icona della finestra |

## Crediti
Creato da **Raffaele Catapano** - [github.com/MrGodLink](https://github.com/MrGodLink)

Se riutilizzi, modifichi o ridistribuisci questo progetto, mantieni la nota di copyright e
cita l'autore originale, come richiesto dalla licenza MIT.

### Altri progetti dell'autore
- [RcFux](https://github.com/MrGodLink/RuFux) - utility grafica (PySide6) per creare chiavette USB avviabili su Linux.
- [CISO-Converter](https://github.com/MrGodLink/CISO-Converter) - strumento desktop (PySide6) per convertire ISO in CSO e CSO in ISO, il formato di immagine disco compresso usato da PSP e dai suoi emulatori.

## Licenza
Il codice sorgente è rilasciato con licenza MIT - vedi [LICENSE](LICENSE).

MIDI Studio dipende da [PySide6](https://doc.qt.io/qtforpython/), con licenza LGPLv3 (oppure licenza commerciale Qt). Viene installato separatamente (con `pip` o dalla distribuzione). Se distribuisci un eseguibile incorporato (per esempio creato con PyInstaller), devi rispettare anche i termini LGPL di PySide6 e Qt.
FluidSynth (LGPL) e FFmpeg (LGPL/GPL, a seconda della build) sono programmi separati richiamati da riga di comando e non sono inclusi in questo repository. I file SoundFont hanno licenze proprie.
