from fastapi import FastAPI, Request
from .mcp_server import mcp, ask_cv, AskCvIn, send_email, SendEmailIn
from mcp.server.stdio import stdio_server
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="MCP CV Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"ok": True}

@app.get("/healthz")
async def healthz():
    return {"ok": True, "mcp": True}

# Simple REST shim for CV chat + email
from .mcp_server import ask_cv, AskCvIn, send_email, SendEmailIn

@app.post("/chat")
def chat(inp: AskCvIn):
    return ask_cv(inp).model_dump()

@app.post("/email/send")
def email_send(inp: SendEmailIn):
    return send_email(inp).model_dump()

# --- Optional MCP endpoint over HTTP stream ---
@app.api_route("/mcp", methods=["POST"])
async def mcp_entry(request: Request):
    # For now: just confirm it's alive
    data = await request.json()
    return {"message": "MCP placeholder", "received": data}