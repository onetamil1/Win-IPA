"""
IPA - Intelligent Personal Assistant

A privacy-first AI-powered personal assistant that monitors your work patterns,
provides health recommendations, and helps manage tasks intelligently.

All data is stored locally. No cloud dependency.
Powered by local Llama 3.2 via Ollama.
"""

__version__ = "0.1.0"
__author__ = "IPA Development Team"

from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
LOGS_DIR = DATA_DIR / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database path
DB_PATH = DATA_DIR / "ipa.db"

