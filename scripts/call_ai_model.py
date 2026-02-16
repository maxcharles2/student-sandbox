#!/usr/bin/env python3
import json
import os
import sys
import requests

API_KEY = os.environ.get("LLM_API_KEY")
if not API_KEY:
  print("Missing LLM_API_KEY env var", file=sys.stderr)
  sys.exit(2)

def read_text(path: str) -> str:
  with open(path, "r", encoding="utf-8") as f:
    return f.read()

def main():
  prompt = read_text("compiled.lcp").strip()
  if not prompt:
    print("compiled.lcp is empty", file=sys.stderr)
    sys.exit(2)

  url = "https://openrouter.ai/api/v1/chat/completions"
  headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/",
    "X-Title": "rc-copilot",
  }

  system = "You are a course assistant in CI. Be concise, specific, and actionable."

  payload = {
    "model": os.environ.get("OPENROUTER_MODEL", "arcee-ai/trinity-large-preview:free"),
    "messages": [
      {"role": "system", "content": system},
      {"role": "user", "content": prompt},
    ],
    "temperature": float(os.environ.get("TEMPERATURE", "0.2")),
    "max_tokens": int(os.environ.get("MAX_TOKENS", "1500")),
  }

  r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
  if r.status_code >= 300:
    # emit markdown so PR comment step can still run
    body = r.text[:600].replace("`", "'")
    print(f"""## AI Review (fallback)

Model call failed.

- HTTP: **{r.status_code}**
- Body (truncated): `{body}`

Try:
- Lower MAX_TOKENS
- Switch OPENROUTER_MODEL
- Check OpenRouter credits/quota
""")
    sys.exit(0)

  data = r.json()
  try:
    out = data["choices"][0]["message"]["content"]
  except Exception:
    out = "Unexpected response shape:\n\n```json\n" + json.dumps(data, indent=2)[:4000] + "\n```"

  print(out)

if __name__ == "__main__":
  main()
