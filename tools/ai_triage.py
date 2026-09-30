"""
AI-assisted failure triage.

Reads the JUnit XML produced by pytest, extracts the failed tests and asks
Claude to group them, suggest a likely root cause (hardware / network /
software / test code) and a next step. Writes a Markdown report that CI
publishes as an artifact.

If no ANTHROPIC_API_KEY is set, it still writes a plain summary, so the
pipeline never breaks because of the AI step.

Usage:  python tools/ai_triage.py reports/junit.xml
"""
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPORT = Path("reports/ai_triage.md")
MODEL = os.getenv("AI_MODEL", "claude-sonnet-5-5")


def collect_failures(junit_path):
    root = ET.parse(junit_path).getroot()
    failures = []
    for case in root.iter("testcase"):
        for tag in ("failure", "error"):
            node = case.find(tag)
            if node is not None:
                failures.append({
                    "test": f"{case.get('classname')}::{case.get('name')}",
                    "message": (node.get("message") or "")[:500],
                    "details": (node.text or "")[-1500:],
                })
    return failures


def ask_ai(failures):
    import anthropic  # imported here so the script works without the SDK

    failures_text = "\n\n".join(
        f"TEST: {f['test']}\nMESSAGE: {f['message']}\nTRACE:\n{f['details']}"
        for f in failures
    )
    prompt = (
        "You are a senior test engineer for RF test equipment. "
        "These automated tests failed in CI. Tests talk to a signal analyzer "
        "over SCPI/TCP and to a web dashboard with Selenium.\n"
        "1) Group failures that share a root cause.\n"
        "2) For each group say if it looks like hardware/instrument, "
        "network, product software or test code, and why.\n"
        "3) Suggest one concrete next debugging step per group.\n"
        "Be concise, use Markdown.\n\n" + failures_text
    )
    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def main(junit_path):
    failures = collect_failures(junit_path)
    REPORT.parent.mkdir(exist_ok=True)

    if not failures:
        REPORT.write_text("# AI triage\n\nAll tests passed. Nothing to triage.\n")
        print("No failures.")
        return

    summary = "\n".join(
        f"- `{f['test']}`: {f['message'].splitlines()[0] if f['message'] else ''}"
        for f in failures
    )
    body = f"# AI triage\n\n## Failed tests ({len(failures)})\n{summary}\n"

    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            body += "\n## AI analysis\n" + ask_ai(failures) + "\n"
        except Exception as exc:  # the AI step must never break CI
            body += f"\n_AI analysis unavailable: {exc}_\n"
    else:
        body += "\n_Set ANTHROPIC_API_KEY to get an AI analysis._\n"

    REPORT.write_text(body)
    print(body)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "reports/junit.xml")
