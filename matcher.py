import math
from collections import Counter

from extractor import extract_skills, flat_skills
from nlp_utils import clean_tokens


def _tfidf(docs):
    n = len(docs)
    df = Counter(w for d in docs for w in set(d))
    idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}
    return [{w: (c / len(d)) * idf[w] for w, c in Counter(d).items()} for d in docs]


def cosine(a, b):
    dot = sum(a[w] * b.get(w, 0) for w in a)
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def match(resume_text, jd_text):
    """Compare resume with a job description.

    skill_percent = matched JD skills / total JD skills * 100
    overall       = 70% skill coverage + 30% TF-IDF cosine similarity
    """
    r, j = clean_tokens(resume_text), clean_tokens(jd_text)
    sim = 0.0
    if r and j:
        vr, vj = _tfidf([r, j])
        sim = cosine(vr, vj)

    res_cat, jd_cat = extract_skills(resume_text), extract_skills(jd_text)
    rs, js = set(flat_skills(res_cat)), set(flat_skills(jd_cat))
    matched, missing, extra = sorted(rs & js), sorted(js - rs), sorted(rs - js)
    coverage = len(matched) / len(js) if js else 0.0

    categories = []
    for cat, skills in jd_cat.items():
        got = [s for s in skills if s in rs]
        categories.append({"category": cat, "required": len(skills), "matched": len(got),
                           "percent": round(len(got) / len(skills) * 100)})

    overall = 0.7 * coverage + 0.3 * sim
    if overall >= 0.75:
        verdict = "Excellent match"
    elif overall >= 0.5:
        verdict = "Good match"
    elif overall >= 0.3:
        verdict = "Partial match"
    else:
        verdict = "Low match"

    return {"jd_skills_found": len(js),
            "skill_percent": round(coverage * 100, 1),
            "text_similarity_percent": round(sim * 100, 1),
            "overall_percent": round(overall * 100, 1),
            "verdict": verdict,
            "matched_skills": matched,
            "missing_skills": missing,
            "extra_skills": extra,
            "categories": categories}
