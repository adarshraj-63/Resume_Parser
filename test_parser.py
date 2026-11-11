import unittest

from extractor import extract_contact, extract_name, extract_skills, parse_resume
from matcher import match
from nlp_utils import read_text

SAMPLE = read_text("sample_resume.txt")
JD = read_text("sample_jd.txt")


class T(unittest.TestCase):
    def test_contact(self):
        c = extract_contact(SAMPLE)
        self.assertEqual(c["email"], "rahul.kumar@gmail.com")
        self.assertIn("98765", c["phone"])
        self.assertIn("github.com/rahulk", c["github"])

    def test_name(self):
        self.assertEqual(extract_name(SAMPLE), "Rahul Kumar")

    def test_skills_no_java_in_javascript(self):
        s = extract_skills("Worked with JavaScript only")
        self.assertNotIn("java", s.get("languages", []))
        self.assertIn("javascript", s["languages"])

    def test_skill_symbols(self):
        self.assertIn("c++", extract_skills("Experienced in C++ and Node.js")["languages"])

    def test_full_parse(self):
        r = parse_resume(SAMPLE)
        self.assertGreaterEqual(len(r["education"]), 2)
        self.assertGreater(r["experience"]["total_years"], 0)
        self.assertEqual(len(r["projects"]), 2)
        self.assertIn("docker", r["skills"]["tools"])

    def test_match_fields(self):
        m = match(SAMPLE, JD)
        self.assertIn("kubernetes", m["missing_skills"])
        self.assertIn("python", m["matched_skills"])
        self.assertTrue(0 < m["skill_percent"] < 100)
        self.assertEqual(m["jd_skills_found"], len(m["matched_skills"]) + len(m["missing_skills"]))
        self.assertTrue(m["categories"])

    def test_perfect_and_zero(self):
        self.assertEqual(match("Python and Docker", "Python and Docker")["skill_percent"], 100.0)
        self.assertEqual(match("I like cooking", "Python and Docker")["skill_percent"], 0.0)

    def test_empty_jd_skills(self):
        self.assertEqual(match(SAMPLE, "Great communication needed")["skill_percent"], 0.0)


if __name__ == "__main__":
    unittest.main()
