import os
import tempfile

from flask import Flask, jsonify, render_template, request

from extractor import parse_resume
from matcher import match
from nlp_utils import read_text

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/analyze")
def analyze():
    f = request.files.get("resume")
    jd = request.form.get("jd", "").strip()
    if not f or not f.filename:
        return jsonify(error="Please upload a resume (PDF or TXT)."), 400
    if len(jd) < 20:
        return jsonify(error="Please paste a job description (at least a few lines)."), 400
    ext = os.path.splitext(f.filename)[1].lower()
    if ext not in (".pdf", ".txt"):
        return jsonify(error="Only PDF or TXT files are supported."), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        f.save(tmp.name)
    try:
        raw = read_text(tmp.name)
    except Exception:
        return jsonify(error="Could not read this file. Is it a valid PDF?"), 422
    finally:
        os.remove(tmp.name)

    if len(raw.strip()) < 30:
        return jsonify(error="No text found. Scanned/image PDFs need OCR."), 422

    result = parse_resume(raw)
    result["job_match"] = match(raw, jd)
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True)
