@echo off
title Starte Anwendung...

:: Ladebalken anzeigen
echo Starte PyQt6 Anwendung...
echo.
echo [████████████████████████████████████████] 100%%
echo.

:: Zum Verzeichnis der Batch-Datei wechseln
cd /d "%~dp0"

:: Anwendung starten und Kommandofenster verstecken
start /min "" python main.py

:: Batch-Fenster nach 2 Sekunden schliessen
timeout /t 2 /nobreak >nul
exit