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
"""i18n.py - UI strings for MIDI Studio (English / Italian).

The audio backend (synth_backend.py) never sends human-readable text: it sends
message keys plus parameters, which are translated here with tr().
"""

LANGUAGES = (("en", "English"), ("it", "Italiano"))
_lang = "en"

STRINGS = {
    "en": {
        "language": "Language:", "btn_ok": "OK", "btn_cancel": "Cancel",
        # main window
        "act_open": "Open MIDI…", "act_open_folder": "Open folder…",
        "act_convert": "Convert to MP3…", "act_settings": "Settings ⚙",
        "playlist": "Playlist", "no_track": "No track loaded", "status_ready": "Ready",
        "menu_play": "Play", "menu_remove": "Remove from playlist",
        "tools_missing_title": "Missing components",
        "tools_missing_text": (
            "The following external tools were not found in the PATH:\n  {tools}\n\n"
            "Installation (Debian/Ubuntu):\n"
            "  sudo apt install fluidsynth ffmpeg fluid-soundfont-gm\n"
            "(or the equivalent packages of your distribution).\n\n"
            "The app will stay open, but playback and conversion will not work "
            "until they are installed."),
        "no_soundfont_status": "No SoundFont found: choose one from Settings → Synthesizer",
        "dlg_open_midi": "Open MIDI files", "dlg_midi_filter": "MIDI files (*.mid *.midi *.kar)",
        "dlg_open_folder": "Open folder", "folder_added": "Added {n} MIDI files from the folder",
        "no_soundfont_title": "No SoundFont",
        "no_soundfont_text": "Select a SoundFont from Settings → Synthesizer.",
        "fluidsynth_missing_title": "FluidSynth not found",
        "fluidsynth_missing_text": "Install FluidSynth and try again (see the warning shown at startup).",
        "rendering": "Rendering '{name}'…", "render_busy": "A rendering is already in progress, please wait.",
        "render_error_status": "Error while rendering", "render_error_title": "FluidSynth error",
        "playback_error": "Playback error: {err}", "settings_updated": "Settings updated",
        "pick_midi_convert": "Choose the MIDI files to convert",
        "tool_missing_title": "Missing tool", "tool_missing_text": "'{tool}' was not found in the PATH.",
        "conv_done_file": "Completed: {name}", "conv_err_file": "Error on {name}: {err}",
        "busy_quit": "A rendering is in progress: wait for it to finish before quitting.",
        # settings dialog
        "dlg_settings": "Settings", "tab_synth": "Synthesizer", "tab_playback": "Playback",
        "grp_soundfont": "SoundFont (timbre)", "btn_browse": "Browse…", "btn_detect": "Detect",
        "sf_hint": ("The SoundFont determines the realism of the piano more than anything else: "
                    "a dedicated piano SoundFont (e.g. Salamander Grand Piano, with several "
                    "velocity layers) sounds much more natural than a generic GM one such as FluidR3."),
        "grp_presets": "Quick presets", "preset_default": "Default",
        "preset_piano": "Realistic piano", "preset_low": "Low resources",
        "grp_quality": "Synthesis quality", "lbl_interp": "Interpolation:",
        "lbl_synth_sr": "Synthesis sample rate:", "lbl_wav_fmt": "Intermediate WAV sample format:",
        "lbl_gain": "Overall gain:", "lbl_poly": "Polyphony (max voices):",
        "lbl_cores": "Synthesis CPU cores:", "lbl_bank": "MIDI Bank Select mode:",
        "interp_none": "None (fastest, audible aliasing)", "interp_linear": "Linear (low quality)",
        "interp_4th": "4th order - FluidSynth default", "interp_7th": "7th order / Sinc - maximum quality",
        "chorus_sine": "Sine (default)", "chorus_triangle": "Triangle",
        "grp_reverb": "Reverb", "rev_room": "Room size", "rev_damp": "Damping",
        "rev_width": "Stereo width", "rev_level": "Level",
        "grp_chorus": "Chorus", "cho_voices": "Number of voices:", "cho_level": "Level",
        "cho_speed": "Speed (Hz)", "cho_depth": "Depth (ms)", "cho_wave": "Waveform:",
        "no_sf_found": "No SoundFont found — use 'Browse…'", "dlg_pick_sf": "Choose a SoundFont",
        "grp_audio_out": "Audio output", "dev_default": "System default device",
        "lbl_audio_card": "Playback sound card:",
        "playback_note": ("Note: the MP3 conversion does not physically go through the sound card "
                          "(it is an internal digital rendering), so it does not use its converters: "
                          "the fidelity of the final file depends on the SoundFont, on the synthesizer "
                          "settings of the other tab and on the MP3 bitrate chosen in the conversion "
                          "window. The sound card only affects the perceived quality while listening "
                          "live in this program."),
        # convert dialog
        "dlg_convert": "Convert to MP3", "files_one": "1 file selected", "files_n": "{n} files selected",
        "grp_dest": "Destination", "grp_mp3": "MP3 quality (LAME)",
        "rb_vbr": "VBR (variable quality, recommended)", "rb_cbr": "CBR (constant bitrate)",
        "vbr_tip": "0 = best quality (~245-320 kbps), 9 = lowest quality",
        "lbl_vbr": "VBR quality (0 = best):", "lbl_cbr": "CBR bitrate:", "lbl_mp3_sr": "MP3 sample rate:",
        "chk_soxr": "High-quality resampling (soxr)", "chk_norm": "Normalize loudness (EBU R128)",
        "dlg_save_mp3": "Save MP3 as", "dlg_dest_dir": "Destination folder",
        "btn_convert": "Convert", "btn_close": "Close", "starting_conv": "Starting conversion…",
        "conv_finished": "Completed: {ok} files converted",
        "conv_finished_err": "Completed: {ok} files converted, {err} with errors",
        "overwrite_title": "Overwrite?", "overwrite_text": "{n} output file(s) already exist and will be overwritten.\n\nContinue?",
        # backend messages
        "be_starting": "Starting FluidSynth…", "be_render_done": "WAV rendering completed.",
        "be_param_ignored": "Parameter not supported by this FluidSynth version, ignored: {params}",
        "be_encoding_soxr": "Encoding MP3 (soxr resampler)…", "be_encoding": "Encoding MP3…",
        "err_render": "FluidSynth failed to produce the WAV file.",
        "err_convert": "FFmpeg failed to create the MP3 file.",
        "err_soundfont_missing": "SoundFont file not found:", "err_unexpected": "Unexpected error:",
    },
    "it": {
        "language": "Lingua:", "btn_ok": "OK", "btn_cancel": "Annulla",
        "act_open": "Apri MIDI…", "act_open_folder": "Apri cartella…",
        "act_convert": "Converti in MP3…", "act_settings": "Impostazioni ⚙",
        "playlist": "Playlist", "no_track": "Nessun brano caricato", "status_ready": "Pronto",
        "menu_play": "Riproduci", "menu_remove": "Rimuovi dalla playlist",
        "tools_missing_title": "Componenti mancanti",
        "tools_missing_text": (
            "I seguenti strumenti esterni non sono stati trovati nel PATH:\n  {tools}\n\n"
            "Installazione (Debian/Ubuntu):\n"
            "  sudo apt install fluidsynth ffmpeg fluid-soundfont-gm\n"
            "(o i pacchetti equivalenti della tua distribuzione).\n\n"
            "L'app resterà aperta, ma riproduzione e conversione non funzioneranno "
            "finché non sono installati."),
        "no_soundfont_status": "Nessun SoundFont trovato: sceglilo da Impostazioni → Sintetizzatore",
        "dlg_open_midi": "Apri file MIDI", "dlg_midi_filter": "File MIDI (*.mid *.midi *.kar)",
        "dlg_open_folder": "Apri cartella", "folder_added": "Aggiunti {n} file MIDI dalla cartella",
        "no_soundfont_title": "Nessun SoundFont",
        "no_soundfont_text": "Seleziona un SoundFont da Impostazioni → Sintetizzatore.",
        "fluidsynth_missing_title": "FluidSynth non trovato",
        "fluidsynth_missing_text": "Installa FluidSynth e riprova (vedi l'avviso iniziale).",
        "rendering": "Rendering di '{name}'…", "render_busy": "Un rendering è già in corso, attendi.",
        "render_error_status": "Errore durante il rendering", "render_error_title": "Errore FluidSynth",
        "playback_error": "Errore di riproduzione: {err}", "settings_updated": "Impostazioni aggiornate",
        "pick_midi_convert": "Scegli i file MIDI da convertire",
        "tool_missing_title": "Strumento mancante", "tool_missing_text": "'{tool}' non trovato nel PATH.",
        "conv_done_file": "Completato: {name}", "conv_err_file": "Errore su {name}: {err}",
        "busy_quit": "Un rendering è in corso: attendi che finisca prima di uscire.",
        "dlg_settings": "Impostazioni", "tab_synth": "Sintetizzatore", "tab_playback": "Riproduzione",
        "grp_soundfont": "SoundFont (timbrica)", "btn_browse": "Sfoglia…", "btn_detect": "Rileva",
        "sf_hint": ("Il SoundFont determina più di ogni altra cosa il realismo del pianoforte: "
                    "un SoundFont pianistico dedicato (es. Salamander Grand Piano, con più velocity "
                    "layer) suona molto più naturale di un GM generico come FluidR3."),
        "grp_presets": "Preset rapidi", "preset_default": "Predefinito",
        "preset_piano": "Piano realistico", "preset_low": "Basse risorse",
        "grp_quality": "Qualità di sintesi", "lbl_interp": "Interpolazione:",
        "lbl_synth_sr": "Frequenza di campionamento sintesi:", "lbl_wav_fmt": "Formato campione WAV intermedio:",
        "lbl_gain": "Gain generale:", "lbl_poly": "Polifonia (voci max):",
        "lbl_cores": "Core CPU sintesi:", "lbl_bank": "Modalità Bank Select MIDI:",
        "interp_none": "Nessuna (più veloce, aliasing udibile)", "interp_linear": "Lineare (bassa qualità)",
        "interp_4th": "4° ordine - default FluidSynth", "interp_7th": "7° ordine / Sinc - qualità massima",
        "chorus_sine": "Sinusoidale (default)", "chorus_triangle": "Triangolare",
        "grp_reverb": "Riverbero", "rev_room": "Dimensione sala", "rev_damp": "Damping",
        "rev_width": "Larghezza stereo", "rev_level": "Livello",
        "grp_chorus": "Chorus", "cho_voices": "Numero linee:", "cho_level": "Livello",
        "cho_speed": "Velocità (Hz)", "cho_depth": "Profondità (ms)", "cho_wave": "Forma d'onda:",
        "no_sf_found": "Nessun SoundFont trovato — usa 'Sfoglia…'", "dlg_pick_sf": "Scegli un SoundFont",
        "grp_audio_out": "Uscita audio", "dev_default": "Dispositivo predefinito di sistema",
        "lbl_audio_card": "Scheda audio di riproduzione:",
        "playback_note": ("Nota: la conversione in MP3 non passa fisicamente attraverso la scheda audio "
                          "(è un rendering digitale interno), quindi non ne sfrutta i convertitori: "
                          "la fedeltà del file finale dipende dal SoundFont, dalle impostazioni del "
                          "sintetizzatore nell'altra scheda e dal bitrate MP3 scelto nella finestra di "
                          "conversione. La scheda audio incide invece sulla qualità percepita durante "
                          "l'ascolto dal vivo in questo programma."),
        "dlg_convert": "Converti in MP3", "files_one": "1 file selezionato", "files_n": "{n} file selezionati",
        "grp_dest": "Destinazione", "grp_mp3": "Qualità MP3 (LAME)",
        "rb_vbr": "VBR (qualità variabile, consigliato)", "rb_cbr": "CBR (bitrate costante)",
        "vbr_tip": "0 = qualità massima (~245-320 kbps), 9 = qualità minima",
        "lbl_vbr": "Qualità VBR (0 = migliore):", "lbl_cbr": "Bitrate CBR:",
        "lbl_mp3_sr": "Frequenza di campionamento MP3:",
        "chk_soxr": "Ricampionamento in alta qualità (soxr)", "chk_norm": "Normalizza il volume (loudness EBU R128)",
        "dlg_save_mp3": "Salva MP3 come", "dlg_dest_dir": "Cartella di destinazione",
        "btn_convert": "Converti", "btn_close": "Chiudi", "starting_conv": "Avvio conversione…",
        "conv_finished": "Completato: {ok} file convertiti",
        "conv_finished_err": "Completato: {ok} file convertiti, {err} con errori",
        "overwrite_title": "Sovrascrivere?", "overwrite_text": "{n} file di destinazione esistono già e verranno sovrascritti.\n\nContinuare?",
        "be_starting": "Avvio FluidSynth…", "be_render_done": "Rendering WAV completato.",
        "be_param_ignored": "Parametro non supportato da questa versione di FluidSynth, ignorato: {params}",
        "be_encoding_soxr": "Codifica MP3 (resampler soxr)…", "be_encoding": "Codifica MP3…",
        "err_render": "FluidSynth non è riuscito a produrre il file WAV.",
        "err_convert": "FFmpeg non è riuscito a creare il file MP3.",
        "err_soundfont_missing": "File SoundFont non trovato:", "err_unexpected": "Errore inatteso:",
    },
}


def set_lang(code):
    global _lang
    _lang = code if code in STRINGS else "en"


def get_lang():
    return _lang


def tr(key, **kw):
    text = STRINGS[_lang].get(key) or STRINGS["en"].get(key) or key
    try:
        return text.format(**kw) if kw else text
    except (KeyError, IndexError, ValueError):
        return text
