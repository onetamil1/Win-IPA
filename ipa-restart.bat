@echo off
REM Restart IPA daemon

python cli.py stop
python cli.py start
