import json
import sys

from extractor import parse_resume
from matcher import match
from nlp_utils import read_text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python cli.py resume.pdf [job_description.txt]")
    raw = read_text(sys.argv[1])
    result = parse_resume(raw)
    if len(sys.argv) > 2:
        result["job_match"] = match(raw, read_text(sys.argv[2]))
    print(json.dumps(result, indent=2, ensure_ascii=False))
