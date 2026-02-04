import re

CEIL_RE = re.compile(r"\b(BKN|OVC|VV)(\d{3})\b")
VIS_MIXED = re.compile(r"\b(\d{1,2})\s(\d/\d)SM\b")
VIS_FRAC  = re.compile(r"\b(\d/\d)SM\b")
VIS_WHOLE = re.compile(r"\b(\d{1,2})SM\b")

def ceiling_ft_from_raw(raw: str):
    best = None
    for m in CEIL_RE.finditer(raw or ""):
        ft = int(m.group(2)) * 100
        best = ft if best is None else min(best, ft)
    return best

def visibility_sm_from_raw(raw: str):
    raw = raw or ""
    m = VIS_MIXED.search(raw)
    if m:
        whole = float(m.group(1))
        num, den = m.group(2).split("/")
        return whole + float(num)/float(den)
    m = VIS_FRAC.search(raw)
    if m:
        num, den = m.group(1).split("/")
        return float(num)/float(den)
    m = VIS_WHOLE.search(raw)
    if m:
        return float(m.group(1))
    return None

def flight_category(ceil_ft, vis_sm):
    if ceil_ft is None or vis_sm is None:
        return "Unknown"
    if ceil_ft < 500 or vis_sm < 1:
        return "LIFR"
    if ceil_ft < 1000 or vis_sm < 3:
        return "IFR"
    if ceil_ft < 3000 or vis_sm < 5:
        return "MVFR"
    return "VFR"
``