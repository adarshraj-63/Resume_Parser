import json
import re
from datetime import date
from pathlib import Path

from nlp_utils import clean_text, named_entities, noun_keywords, summarize

SKILLS = json.loads((Path(__file__).parent / "skills.json").read_text())
ALIASES = {"js": "javascript", "reactjs": "react", "react.js": "react", "nodejs": "node.js",
           "node": "node.js", "ml": "machine learning", "dl": "deep learning",
           "sklearn": "scikit-learn", "postgres": "postgresql", "mongo": "mongodb",
           "py": "python", "restful api": "rest api", "expressjs": "express"}

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
PHONE = re.compile(r"(?<!\d)(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3,5}\)?[\s-]?)?\d{3,5}[\s-]?\d{4,5}(?!\d)")
LINKEDIN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+/?", re.I)
GITHUB = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[\w-]+/?", re.I)

HEADERS = {
    "summary": {"summary", "objective", "profile", "about me", "career objective"},
    "skills": {"skills", "technical skills", "key skills", "technologies", "skill set"},
    "experience": {"experience", "work experience", "professional experience",
                   "employment history", "internships", "internship"},
    "education": {"education", "academic background", "academics", "qualifications"},
    "projects": {"projects", "academic projects", "personal projects"},
    "certifications": {"certifications", "certificates", "courses"},
}

DEGREE = re.compile(
    r"\b(b\.?\s?tech|m\.?\s?tech|b\.?\s?e\b|m\.?\s?e\b|b\.?\s?sc|m\.?\s?sc|bca|mca|mba|ph\.?d|"
    r"bachelor(?:s)?(?: of [a-z ]+)?|master(?:s)?(?: of [a-z ]+)?|diploma|"
    r"12th|10th|intermediate|higher secondary|secondary)\b", re.I)
CGPA = re.compile(r"(?:cgpa|gpa)\s*[:\-]?\s*(\d{1,2}(?:\.\d{1,2})?)|(\d{2}(?:\.\d+)?)\s*%", re.I)

MON = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"
_DATE = rf"(?:(?:{MON})[a-z]*\.?\s+\d{{4}}|\d{{4}})"
RANGE = re.compile(rf"({_DATE})\s*(?:-|–|—|to)\s*({_DATE}|present|current|now)", re.I)
YEARS_EXP = re.compile(r"(\d+(?:\.\d+)?)\+?\s*years?\s+(?:of\s+)?experience", re.I)
MONTHS = {m: i + 1 for i, m in enumerate(MON.split("|"))}


def split_sections(text):
    """Rule-based segmentation: header lines open a new slot."""
    sections, current = {"header": []}, "header"
    for line in text.split("\n"):
        key = line.strip().lower().rstrip(":").strip()
        found = next((s for s, names in HEADERS.items() if key in names), None)
        if found and len(key) < 40:
            current = found
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def extract_contact(text):
    emails = EMAIL.findall(text)
    phones = []
    for m in PHONE.finditer(text):
        digits = re.sub(r"\D", "", m.group())
        if 10 <= len(digits) <= 13 and not re.fullmatch(r"(19|20)\d{2}(19|20)\d{2}", digits):
            phones.append(m.group().strip())
    li, gh = LINKEDIN.search(text), GITHUB.search(text)
    return {"email": emails[0] if emails else None,
            "phone": phones[0] if phones else None,
            "linkedin": li.group() if li else None,
            "github": gh.group() if gh else None}


def extract_name(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()][:6]
    for l in lines:
        if "@" in l or re.search(r"\d", l) or l.lower() in sum(map(list, HEADERS.values()), []):
            continue
        if re.fullmatch(r"[A-Za-z][A-Za-z.' -]+", l) and 2 <= len(l.split()) <= 4:
            return l.title() if l.isupper() else l
    people = named_entities(" ".join(lines))["PERSON"]
    return people[0] if people else None


def extract_skills(text):
    low = text.lower()
    found = {}
    for category, skills in SKILLS.items():
        for sk in skills:
            if re.search(rf"(?<![\w+#]){re.escape(sk)}(?![\w+#])", low):
                found.setdefault(category, []).append(sk)
    for alias, real in ALIASES.items():
        if re.search(rf"(?<![\w+#.]){re.escape(alias)}(?![\w+#])", low):
            for category, skills in SKILLS.items():
                if real in skills and real not in found.get(category, []):
                    found.setdefault(category, []).append(real)
    return {k: sorted(v) for k, v in found.items()}


def flat_skills(skill_dict):
    return sorted({s for v in skill_dict.values() for s in v})


def extract_education(sections, text):
    block = sections.get("education") or text
    out = []
    for line in block.split("\n"):
        d = DEGREE.search(line)
        if d:
            years = re.findall(r"(?:19|20)\d{2}", line)
            score = CGPA.search(line)
            out.append({"degree": d.group().strip(), "line": line.strip(),
                        "year": years[-1] if years else None,
                        "score": next((g for g in score.groups() if g), None) if score else None})
    return out


def _to_ym(s):
    s = s.lower().strip()
    if s in ("present", "current", "now"):
        t = date.today()
        return t.year, t.month
    m = re.match(rf"({MON})[a-z]*\.?\s+(\d{{4}})", s)
    if m:
        return int(m.group(2)), MONTHS[m.group(1)]
    return int(s), 1


def extract_experience(sections, text):
    block = sections.get("experience", "")
    spans = []
    for a, b in RANGE.findall(block):
        (y1, m1), (y2, m2) = _to_ym(a), _to_ym(b)
        s, e = y1 * 12 + m1, y2 * 12 + m2
        if e >= s:
            spans.append((s, e))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    months = sum(e - s for s, e in merged)
    stated = YEARS_EXP.search(text)
    years = round(months / 12, 1) if months else (float(stated.group(1)) if stated else 0.0)
    ents = named_entities(block) if block else {"ORGANIZATION": [], "GPE": []}
    return {"total_years": years, "date_ranges_found": len(spans),
            "organizations": ents["ORGANIZATION"], "locations": ents["GPE"],
            "details": [l.strip() for l in block.split("\n") if l.strip()][:15]}


def parse_resume(raw_text):
    text = clean_text(raw_text)
    sections = split_sections(text)
    skills = extract_skills(text)
    return {
        "name": extract_name(text),
        "contact": extract_contact(text),
        "summary": sections.get("summary") or summarize(text),
        "skills": skills,
        "education": extract_education(sections, text),
        "experience": extract_experience(sections, text),
        "projects": [l.strip("- ").strip() for l in sections.get("projects", "").split("\n") if l.strip()],
        "certifications": [l.strip("- ").strip() for l in sections.get("certifications", "").split("\n") if l.strip()],
        "keywords": noun_keywords(text),
    }
