#!/usr/bin/env python3
"""
MP3 Tag Checker – GUI zum Pruefen und Reparieren von ID3-Tags.

Projekt:     MP3 Tag Checker
Modul:       app.py
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
Start der grafischen Oberflaeche inkl. Kommandozeilen-Parametern,
zentraler Fehlerbehandlung und Fehler-Logging. Schreibt nur nach
Bestaetigung; jeder Schreibvorgang wird gesichert.

Historie
--------
Version 1.11.0 – 2026-08-14 – CLI --help/--version/--Ende/--no-log, Python 3.13
Version 1.12.0 – 2026-08-18 – Styleguide 1.4.0: Dateikopf Pflichtfelder

Aufruf / Nutzung
----------------
  python app.py --help
  python app.py --version
  python app.py --Ende
  python app.py --no-log
"""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ERROR_LOG = BASE_DIR / "error.log"

PROGRAM_NAME = "MP3 Tag Checker"
DESCRIPTION = (
    "Prueft und repariert die ID3-Tags einer MP3-Bibliothek. Die Anwendung"
    " scannt, schlaegt Aenderungen vor und schreibt nur nach Bestaetigung;"
    " jeder Schreibvorgang wird gesichert und ist umkehrbar.")
EXAMPLES = """Beispiele:
  run.bat                Start ueber das Startskript (empfohlen)
  python app.py          Start der grafischen Oberflaeche
  python app.py --Ende   Start mit Abfrage am Programmende
  python app.py --no-log Start ohne Fehler-Logdatei (error.log)
"""

# Durch --no-log abschaltbar (Style-Guide: Logging per Parameter schaltbar).
_logging_enabled = True


def read_version_info():
    """Liest Versionsnummer und Datum aus version.json.

    Beschreibung: Liest Versionsnummer und Datum aus version.json.
    Parameter: keine.
    Rueckgabewert: Tupel (version, datum) als Strings.
    Fehlerfaelle: fehlende/defekte Datei liefert ("0.0.0", "") - es wird
    nie eine Ausnahme ausgeloest.
    Beispiel: read_version_info() -> ("1.12.0", "2026-08-18")
    """
    try:
        data = json.loads((BASE_DIR / "version.json")
                          .read_text(encoding="utf-8-sig"))
        version = str(data.get("version", "0.0.0"))
        date = next((str(e.get("date", "")) for e in data.get("changelog", [])
                     if str(e.get("version")) == version), "")
        return version, date
    except (OSError, json.JSONDecodeError):
        return "0.0.0", ""


def parse_args(argv):
    """Wertet die Kommandozeilen-Parameter aus.

    Parameter: argv - Liste der Argumente (ohne Programmname).
    Rueckgabewert: argparse.Namespace mit den Feldern ende und no_log.
    Fehlerfaelle: unbekannte Parameter beenden das Programm mit einer
    Fehlermeldung und einem Hinweis auf --help (Exit-Code 2).
    Beispiel: parse_args(["--Ende"]).ende -> True
    """
    version, date = read_version_info()
    parser = argparse.ArgumentParser(
        prog="app.py", add_help=False,
        description="%s %s\n\n%s" % (PROGRAM_NAME, version, DESCRIPTION),
        epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-h", "--help", action="help",
                        help="diese Hilfe anzeigen und beenden")
    parser.add_argument("--version", action="version",
                        version="%s %s (%s)" % (PROGRAM_NAME, version, date),
                        help="Versionsnummer und Datum anzeigen und beenden")
    parser.add_argument("-E", "--Ende", dest="ende", action="store_true",
                        help="am Programmende auf einen Tastendruck warten")
    parser.add_argument("--no-log", dest="no_log", action="store_true",
                        help="Fehler-Logging in error.log abschalten")
    return parser.parse_args(argv)


def _log_error(exc_type, exc, tb):
    """Schreibt eine Ausnahme nach error.log (UTF-8, Zeitstempel
    YYYY-MM-DD HH:MM:SS) und auf stderr; gibt bei PySide6-Ladefehlern
    einen Hinweis auf das fehlende VC++-Redistributable aus."""
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    if _logging_enabled:
        try:
            with ERROR_LOG.open("a", encoding="utf-8") as f:
                f.write("\n=== %s ===\n%s"
                        % (time.strftime("%Y-%m-%d %H:%M:%S"), text))
        except OSError:
            pass
    sys.stderr.write(text)
    if "DLL load failed" in text or "shiboken" in text.lower():
        sys.stderr.write(
            "\nHINT: PySide6 could not load its libraries. This usually means"
            "\nthe 'Microsoft Visual C++ Redistributable (x64)' is missing -"
            "\ninstall it from https://aka.ms/vs/17/release/vc_redist.x64.exe"
            "\nand start the app again.\n")


def _install_excepthook():
    """Log unexpected errors to error.log and show them, instead of dying silently."""
    def hook(exc_type, exc, tb):
        _log_error(exc_type, exc, tb)
        try:
            from PySide6.QtWidgets import QApplication, QMessageBox
            if QApplication.instance():
                QMessageBox.critical(
                    None, "Unexpected error",
                    "Something went wrong (details in error.log):\n\n%s" % exc)
        except Exception:
            pass
    sys.excepthook = hook


def _wait_for_key():
    """Wartet am Programmende auf eine Eingabe (Parameter --Ende / -E)."""
    try:
        input('Programmende: "Hit any Key or Enter"')
    except (EOFError, KeyboardInterrupt):
        pass


def main():
    """Startet die Qt-Anwendung mit Konfiguration, Theme und Hauptfenster.

    Parameter: keine (die Kommandozeile ist bereits ausgewertet).
    Rueckgabewert: Exit-Code der Qt-Ereignisschleife (0 = normal beendet).
    Fehlerfaelle: Ausnahmen beim Start werden vom Aufrufer geloggt.
    """
    from PySide6.QtWidgets import QApplication

    from mp3lib.gui.main_window import MainWindow
    from mp3lib.settings import load_config

    from mp3lib.gui.common import apply_field_labels, apply_theme

    app = QApplication(sys.argv[:1])
    app.setStyle("Fusion")
    cfg = load_config()
    apply_theme(cfg["settings"].get("theme", "auto"))
    apply_field_labels(cfg["settings"])
    win = MainWindow(cfg)
    win.show()
    return app.exec()


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    _logging_enabled = not args.no_log
    _install_excepthook()
    exit_code = 0
    try:
        exit_code = main()
    except SystemExit as e:
        exit_code = e.code if isinstance(e.code, int) else 1
    except Exception:
        # startup errors (imports, config, window construction) land here
        _log_error(*sys.exc_info())
        exit_code = 1
    if args.ende:
        _wait_for_key()
    sys.exit(exit_code)
