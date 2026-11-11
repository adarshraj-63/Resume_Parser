# AI Resume Analyzer (NLP)

Upload a resume + paste a job description -> parsed profile, matched/missing skills, skill match percentage.

Libraries: nltk, numpy, pypdf, flask.

## Setup (Windows PowerShell)
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt

## Run
    python app.py          # open http://127.0.0.1:5000
    python cli.py sample_resume.txt sample_jd.txt
    python -m unittest -v

Skill percentage = matched JD skills / total JD skills found in the JD.
Overall score = 70% skill coverage + 30% TF-IDF cosine similarity.
Add your own skills in skills.json. Scanned PDFs are not supported (need OCR).
