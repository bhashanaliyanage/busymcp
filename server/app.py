import json
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

@app.post("/mcp")
async def mcp_entry(request: Request):
    try:
        # parse incoming JSON-RPC request
        data = await request.json()

        # Log the incoming request nicely
        print("\n=== MCP Request ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("==================\n")

        # handle it using FastMCP's internal handle method
        response = mcp.handle(data)  # <-- handle() is the correct method

        # Optionally log the response too
        print("\n=== MCP Response ===")
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print("===================\n")

        return response

    except Exception as e:
        # return proper JSON-RPC error if something goes wrong
        print("MCP endpoint error:", e)
        return {
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": data.get("id") if isinstance(data, dict) else None,
        }