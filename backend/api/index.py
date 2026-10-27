import sys
from pathlib import Path

# Make the backend root importable when running as a Vercel function
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.main import app  # noqa: E402,F401