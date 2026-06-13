#!/usr/bin/env python3
"""
Entry point per la dashboard Streamlit del trading-agent.

Uso:
    python scripts/run_dashboard.py
    oppure:
    streamlit run tradingagents/dashboard/app.py
"""

import sys
import os
from pathlib import Path

# Aggiungi la repo root al path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")

from tradingagents.dashboard.app import main

if __name__ == "__main__":
    main()
