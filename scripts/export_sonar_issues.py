import json
import os
from pathlib import Path

import requests

url = "https://sonarcloud.io/api/issues/search"

params = {
    "componentKeys": "devsetgo_pydantic-schemaforms",
    "issueStatuses": "OPEN",
    "ps": 500,
    "p": 1,
}

token = os.environ.get("SONAR_TOKEN")

if token:
    response = requests.get(url, params=params, auth=(token, ""))
else:
    response = requests.get(url, params=params)

response.raise_for_status()

data = response.json()

lines = ["# SonarCloud Issues\n"]

for i, issue in enumerate(data.get("issues", []), 1):
    lines.append(f"## {i}. {issue.get('message')}")
    lines.append(f"- Rule: `{issue.get('rule')}`")
    lines.append(f"- Severity: `{issue.get('severity')}`")
    lines.append(f"- Type: `{issue.get('type')}`")
    lines.append(f"- File: `{issue.get('component')}`")
    lines.append(f"- Line: `{issue.get('line', 'N/A')}`")
    lines.append("")

Path("sonarcloud-issues.md").write_text("\n".join(lines))

print(f"Exported {len(data.get('issues', []))} issues")
