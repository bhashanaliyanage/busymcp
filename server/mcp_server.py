from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from rapidfuzz import process, fuzz
import json, pathlib
from .emailer import send_email_smtp

mcp = FastMCP("cv-server")

CV_PATH = pathlib.Path(__file__).parent / "cv_data.json"
CV = json.loads(CV_PATH.read_text(encoding="utf-8"))

# --- Resources: expose cv.json so hosts can inspect context ---
@mcp.resource("cv:json")
def cv_resource():
    return {
        "mimeType": "application/json",
        "text": json.dumps(CV, ensure_ascii=False, indent=2)
    }

# --- Tool: ask_cv(question) ---
class AskCvIn(BaseModel):
    question: str = Field(description="Natural language question about the CV")

class AskCvOut(BaseModel):
    answer: str

@mcp.tool("ask_cv")
def ask_cv(inp: AskCvIn) -> AskCvOut:
    q = inp.question.lower()

    # Profile / intro
    if "name" in q:
        return AskCvOut(answer=CV["profile"]["name"])
    if "title" in q or "who are you" in q or "position" in q:
        return AskCvOut(answer=f"{CV['profile']['title']} — {CV['profile']['summary']}")

    # Contact info
    if "email" in q:
        return AskCvOut(answer=f"Email: {CV['contact']['email']}")
    if "phone" in q or "number" in q:
        return AskCvOut(answer=f"Phone: {CV['contact']['phone']}")
    if "location" in q or "where" in q or "based" in q:
        return AskCvOut(answer=f"Location: {CV['contact']['location']}")

    # Experience (summary or detailed)
    if "experience" in q or "role" in q or "job" in q or "position" in q:
        exp_lines = []
        detailed = "detail" in q or "more" in q or "deep" in q
        if "last" in q or "latest" in q or "current" in q:
            last = CV["experience"][0]
            if detailed:
                highlights = "\n  - " + "\n  - ".join(last.get("highlights", []))
                ans = (
                    f"{last['role']} at {last['company']} "
                    f"({last['start']} – {last['end']})\nHighlights:{highlights}"
                )
            else:
                ans = f"{last['role']} at {last['company']} ({last['start']} – {last['end']})."
            return AskCvOut(answer=ans)
        else:
            for e in CV["experience"]:
                if detailed:
                    highlights = "\n  - " + "\n  - ".join(e.get("highlights", []))
                    exp_lines.append(
                        f"{e['role']} at {e['company']} ({e['start']} – {e['end']})\nHighlights:{highlights}"
                    )
                else:
                    exp_lines.append(
                        f"{e['role']} at {e['company']} ({e['start']} – {e['end']})"
                    )
            return AskCvOut(answer="Experience:\n" + "\n".join(exp_lines))

    # Skills / stack
    if "skills" in q or "stack" in q or "tech" in q or "technologies" in q:
        all_skills = []
        for s in CV["skills"]:
            all_skills.append(
                f"Languages: {', '.join(s['languages'])}. "
                f"Frameworks: {', '.join(s['frameworks'])}. "
                f"Web: {', '.join(s['web'])}. "
                f"Databases: {', '.join(s['databases'])}. "
                f"Tools: {', '.join(s['tools'])}."
            )
        return AskCvOut(answer="\n".join(all_skills))

    # Education
    if "education" in q or "degree" in q or "study" in q or "university" in q or "school" in q:
        ed_lines = []
        for ed in CV["education"]:
            ed_lines.append(
                f"{ed['degree']} at {ed['school']} ({ed['start']} – {ed['end']}). "
                f"Focus areas: {', '.join(ed['focus'])}."
            )
        return AskCvOut(answer="Education:\n" + "\n".join(ed_lines))

    # Languages spoken
    if "speak" in q or "language" in q:
        langs = ", ".join(CV["languagesSpoken"])
        return AskCvOut(answer=f"Languages spoken: {langs}")

    # Projects
    if "project" in q:
        detailed = "detail" in q or "more" in q or "deep" in q
        projects = []
        for p in CV["projects"]:
            if detailed:
                projects.append(f"{p['name']}\n  Tech: {', '.join(p['tech'])}")
            else:
                projects.append(f"{p['name']} (Tech: {', '.join(p['tech'])})")
        return AskCvOut(answer="Projects:\n" + "\n".join(projects))

    # Fuzzy search over projects + experience highlights
    corpus = []
    for p in CV["projects"]:
        corpus.append(f"{p['name']} | tech: {', '.join(p['tech'])}")
    for e in CV["experience"]:
        for h in e.get("highlights", []):
            corpus.append(h)

    best = process.extractOne(q, corpus, scorer=fuzz.partial_ratio)
    if best and best[1] > 60:
        return AskCvOut(answer=best[0])

    # Default: profile summary
    return AskCvOut(answer=CV["profile"]["summary"])


# --- Tool: send_email(recipient, subject, body) ---
class SendEmailIn(BaseModel):
    recipient: str
    subject: str
    body: str

class SendEmailOut(BaseModel):
    ok: bool
    error: str | None = None

@mcp.tool("send_email")
def send_email(inp: SendEmailIn) -> SendEmailOut:
    result = send_email_smtp(inp.recipient, inp.subject, inp.body)
    return SendEmailOut(ok=result.get("ok", False), error=result.get("error"))
