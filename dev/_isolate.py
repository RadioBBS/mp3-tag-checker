"""
MP3 Tag Checker – Leitet Testdaten in ein Temp-Verzeichnis um.

Projekt:     MP3 Tag Checker
Modul:       dev/_isolate.py
Version:     1.12.0
Stand:       2026-08-18
Abhaengig:   Python >= 3.10; mutagen>=1.47; Pillow>=11.0; PySide6>=6.8; requests>=2.32
Bezug:       requirements.txt
Lizenz:      MIT
Upstream:    https://github.com/DarkKoNO/mp3-tag-checker (Jakub Konopasek)
Erstellt mit: Cursor Grok 4.6
Autor:       Frank Heider / RadioBBS

Beschreibung
------------
Import this FIRST in any dev test/script that imports mp3lib, so all user
data (config.json, themes.json, library databases) is redirected to a throwaway
temp dir. This guarantees a test can never read or write the real config or
libraries. See mp3lib/settings.py (DATA_DIR) and dev/README.md.

    import _isolate  # noqa: F401  -- must come before importing mp3lib

Historie
--------
Version 1.11.0 – 2026-08-14 – CLI --help/--version/--Ende, Python 3.13
Version 1.12.0 – 2026-08-18 – Styleguide 1.4.0: Dateikopf Pflichtfelder

Aufruf / Nutzung
----------------
  Siehe app.py --help
"""
import os
import tempfile

os.environ.setdefault("MP3TAGGER_DATA_DIR",
                      tempfile.mkdtemp(prefix="mp3tagger-test-"))
