import re
from collections import Counter
from pathlib import Path

STOP = set("""a an the and or but if because as until while of at by for with about against between into through
during before after above below to from up down in out on off over under again further then once here there when
where why how all any both each few more most other some such no nor not only own same so than too very can will
just should now i me my we our you your he him his she her it its they them their what which who whom this that
these those am is are was were be been being have has had having do does did doing would could also etc""".split())

ORG_WORDS = {"inc", "ltd", "limited", "pvt", "llc", "corp", "technologies", "solutions", "systems", "labs",
             "university", "institute", "college", "school", "bank", "consulting", "services", "infosys",
             "tcs", "wipro", "google", "microsoft", "amazon", "accenture", "cognizant", "nit", "iit"}
CITIES = {"bangalore", "bengaluru", "patna", "delhi", "mumbai", "pune", "hyderabad", "chennai",
          "kolkata", "noida", "gurgaon", "ranchi", "jaipur", "lucknow", "india"}


def read_text(path):
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join((pg.extract_text() or "") for pg in PdfReader(str(p)).pages)
    if p.suffix.lower() == ".txt":
        return p.read_text(encoding="utf-8", errors="ignore")
    raise ValueError("Only .pdf and .txt files are supported")


def clean_text(text):
    text = text.replace("\r", "\n")
    text = re.sub(r"[•●▪◦►■]", "-", text)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def sent_split(text):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z])|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def tokens(text):
    return [t.lower() for t in re.findall(r"[A-Za-z]+", text)]


def remove_stopwords(toks):
    return [t for t in toks if t not in STOP and len(t) > 2]


def _lemma(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith(("sses", "shes", "ches", "xes")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


def lemmatize(toks):
    return [_lemma(t) for t in toks]


def clean_tokens(text):
    return lemmatize(remove_stopwords(tokens(text)))


def noun_keywords(text, top=10):
    words = [w for w in tokens(text)
             if w not in STOP and len(w) > 3 and not w.endswith(("ly", "ing", "ed"))]
    return [w for w, _ in Counter(lemmatize(words)).most_common(top)]


def summarize(text, n=2):
    sents = [s for s in sent_split(text) if len(s.split()) >= 6]
    if not sents:
        return ""
    freq = Counter(clean_tokens(text))
    scored = []
    for i, s in enumerate(sents):
        words = clean_tokens(s)
        scored.append((sum(freq[w] for w in words) / (len(words) or 1), i, s))
    best = sorted(scored, reverse=True)[:n]
    return " ".join(s for _, _, s in sorted(best, key=lambda x: x[1]))


def named_entities(text, labels=("PERSON", "ORGANIZATION", "GPE")):
    out = {l: [] for l in labels}
    for m in re.finditer(r"\b[A-Z][A-Za-z&.]+(?:\s+[A-Z][A-Za-z&.]+)*", text):
        phrase = m.group().strip(". ")
        words = [w.lower().strip(".") for w in phrase.split()]
        if any(w in CITIES for w in words):
            label = "GPE"
        elif any(w in ORG_WORDS for w in words):
            label = "ORGANIZATION"
        elif 2 <= len(words) <= 3:
            label = "PERSON"
        else:
            continue
        if phrase not in out[label]:
            out[label].append(phrase)
    return out