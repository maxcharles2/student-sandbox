#!/usr/bin/env python3
import json
import os
import sys
import textwrap
import requests

API_KEY = os.environ.get("LLM_API_KEY")
if not API_KEY:
  print("Missing LLM_API_KEY env var", file=sys.stderr)
  sys.exit(2)

def read_text(path: str) -> str:
  with open(path, "r", encoding="utf-8") as f:
    return f.read()

def main():
  prd = read_text("prd.md")
  guidance = read_text("course-context/context/prd_guidance.md")
  template = read_text("course-context/templates/prd_template.md")

  system = "You are a course assistant. Provide concise, actionable feedback. Do not mention policies."
  user = textwrap.dedent(f"""
  Use the following CANON guidance and template to review the student's PRD.

  --- CANON: Guidance ---
  {guidance}

  --- CANON: Template ---
  {template}

  --- STUDENT: PRD ---
  {prd}

  Return Markdown with these sections:
  1) Checklist (are required sections present?)
  2) Top issues (max 5)
  3) Suggested edits (diff-style blocks)
  4) Missing acceptance criteria / tests
  5) Questions (max 5)
  """).strip()

  url = "https://openrouter.ai/api/v1/chat/completions"
  headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    # Recommended by OpenRouter (helps attribution; safe placeholders)
    "HTTP-Referer": "https://github.com/",
    "X-Title": "student-sandbox-ai-review",
  }

  payload = {
    "model": "arcee-ai/trinity-large-preview:free",
    "messages": [
      {"role": "system", "content": system},
      {"role": "user", "content": user},
    ],
    "temperature": 0.2,
  }

  r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
  if r.status_code >= 300:
    print(f"OpenRouter error {r.status_code}:\n{r.text}", file=sys.stderr)
    sys.exit(3)

  data = r.json()
  try:
    out = data["choices"][0]["message"]["content"]
  except Exception:
    out = f"Unexpected response shape:\n{json.dumps(data, indent=2)[:4000]}"

  print(out)

if __name__ == "__main__":
  main()
