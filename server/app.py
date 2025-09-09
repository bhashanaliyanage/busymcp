from fastapi import FastAPI, Request
from .mcp_server import ask_cv, AskCvIn, send_email, SendEmailIn, mcp
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

@app.api_route("/mcp", methods=["POST"])
async def mcp_entry(request: Request):
    try:
        # Parse incoming JSON-RPC request
        data = await request.json()

        # Handle it using FastMCP
        response = mcp.handle_json(data)  # returns proper MCP JSON-RPC response

        return response

    except Exception as e:
        # Return error in JSON-RPC format if something goes wrong
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": data.get("id") if isinstance(data, dict) else None,
        }