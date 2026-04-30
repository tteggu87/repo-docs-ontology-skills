from pathlib import Path
from .markdown import parse_markdown


def parse_report_source(
    path: Path,
    profile_id: str = "report-consistency-analysis",
    source_family_id: str = "report-md-txt",
    raw_path: str | None = None,
):
    return parse_markdown(path, profile_id, source_family_id, unit_kind="report_section", raw_path=raw_path)
