from pathlib import Path
from .markdown import parse_markdown

def parse_education_source(path: Path, profile_id: str = "education-analysis", source_family_id: str = "education-md-txt"):
    return parse_markdown(path, profile_id, source_family_id, unit_kind="education_section")
