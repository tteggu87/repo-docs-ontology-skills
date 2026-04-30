from pathlib import Path
from .markdown import parse_markdown

def parse_email_source(path: Path, profile_id: str = "email-analysis", source_family_id: str = "email-md-txt"):
    parsed = parse_markdown(path, profile_id, source_family_id, unit_kind="email_message")
    for u in parsed.units:
        txt=u["text"]
        for line in txt.splitlines()[:6]:
            if line.lower().startswith("from:"): u["author_name"]=line.split(":",1)[1].strip()
            if line.lower().startswith("subject:"): u["subject"]=line.split(":",1)[1].strip()
            if line.lower().startswith("thread-id:"): u["thread_id"]=line.split(":",1)[1].strip()
            if line.lower().startswith("date:"): u["timestamp"]=line.split(":",1)[1].strip()
    return parsed
