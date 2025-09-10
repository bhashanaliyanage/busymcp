import json
from fastapi import FastAPI, Request
from .mcp_server import ask_cv, AskCvIn, send_email, SendEmailIn, cv_resource
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from fastapi.responses import StreamingResponse

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


@app.post("/chat")
def chat(inp: AskCvIn):
    return ask_cv(inp).model_dump()


@app.post("/email/send")
def email_send(inp: SendEmailIn):
    return send_email(inp).model_dump()


# ---- Minimal JSON-RPC router for MCP over HTTP ----
@app.post("/mcp")
async def mcp_http(request: Request):
    data = await request.json()
    rpc_id = data.get("id")
    method = data.get("method")
    params = data.get("params", {}) or {}

    try:
        # 1) tools/list
        if method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "ask_cv",
                        "description": "Ask questions about the CV.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"question": {"type": "string"}},
                            "required": ["question"],
                        },
                    },
                    {
                        "name": "send_email",
                        "description": "Send an email (recipient, subject, body).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "recipient": {"type": "string"},
                                "subject": {"type": "string"},
                                "body": {"type": "string"},
                            },
                            "required": ["recipient", "subject", "body"],
                        },
                    },
                ]
            }
            return {"jsonrpc": "2.0", "id": rpc_id, "result": result}

        # 2) tools/call
        if method == "tools/call":
            name = params.get("name")
            args = params.get("arguments", {}) or {}

            if name == "ask_cv":
                out = ask_cv(AskCvIn(**args))
                # MCP "content" response: text payload
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {"content": [{"type": "text", "text": out.answer}]},
                }

            if name == "send_email":
                out = send_email(SendEmailIn(**args))
                text = (
                    "Email sent."
                    if out.ok
                    else f"Failed: {out.error or 'unknown error'}"
                )
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {"content": [{"type": "text", "text": text}]},
                }

            # unknown tool
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {"code": -32601, "message": f"Unknown tool: {name}"},
            }

        # 3) resources/list
        if method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "resources": [{"uri": "cv:json", "mimeType": "application/json"}]
                },
            }

        # 4) resources/read
        if method == "resources/read":
            uri = params.get("uri")
            if uri != "cv:json":
                return {
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {"code": -32602, "message": f"Unknown resource: {uri}"},
                }
            blob = (
                cv_resource()
            )  # should return {"mimeType": "...", "text": "..."} or similar
            # Normalizing to MCP "content" style
            payload = blob.get("text") or json.dumps(blob)
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {"content": [{"type": "text", "text": payload}]},
            }

        # Unknown method
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }

    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32603, "message": str(e)},
        }


# Your existing JSON-RPC dispatcher:
async def handle_rpc(payload: dict) -> dict:
    # ... route tools/list, tools/call, resources/list, resources/read ...
    return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {}}  # demo


@app.get("/mcp/sse")
async def mcp_sse(request: Request):
    # Very simple SSE loop: read events from client via a query param "q" isn’t viable,
    # so in a real implementation you’d use a bidirectional channel:
    # - Some inspectors POST first to open a session and then stream.
    # - For a minimal demo, we can echo a tools/list once connected.

    async def event_stream():
        # Example: immediately send a tools/list result when connected
        yield "event: message\n"
        yield "data: " + json.dumps(
            {
                "jsonrpc": "2.0",
                "id": "hello",
                "result": {
                    "tools": [
                        {
                            "name": "ask_cv",
                            "description": "Ask questions about the CV.",
                        },
                        {"name": "send_email", "description": "Send an email"},
                    ]
                },
            }
        ) + "\n\n"

        # Keep the stream alive (heartbeat)
        while True:
            if await request.is_disconnected():
                break
            yield "event: ping\ndata: {}\n\n"
            await asyncio.sleep(15)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
