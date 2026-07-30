# Helper Functions
from pathlib import Path


def allowed_file(filename: str) -> bool:

    return Path(filename).suffix.lower() == ".pdf"