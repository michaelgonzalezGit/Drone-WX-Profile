import re

TOPS_RE = re.compile(r"\bTOPS?\s?(\d{2,5})\b", re.IGNORECASE)
BASE_RE = re.compile(r"\bBASES?\s?(\d{2,5})\b", re.IGNORECASE)

def extract_bases_tops(text: str):
    text = text or ""
    bases = [int(x) for x in BASE_RE.findall(text)]
    tops  = [int(x) for x in TOPS_RE.findall(text)]
    return bases, tops