"""Makes `from finance_helpers import ...` resolve the same way it does for
every agent (see backend/main.py's identical sys.path.append)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agents"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
