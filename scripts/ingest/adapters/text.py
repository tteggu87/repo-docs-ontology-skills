from pathlib import Path
from .markdown import parse_markdown

def parse_text(path: Path, profile_id: str, source_family_id: str, unit_kind: str = "paragraph"):
    return parse_markdown(path, profile_id, source_family_id, unit_kind)
