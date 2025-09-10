import asyncio, inspect, json
from types import SimpleNamespace
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from .mcp_server import ask_cv, AskCvIn, send_email, SendEmailIn, cv_resource

app = FastAPI(title="MCP CV Server")

MCP_PROTOCOL = "2025-03-26"  # current spec version

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def mcp_response(id_, result=None, error=None):
    body = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        body["error"] = error
    else:
        body["result"] = result
    return JSONResponse(body)

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


@app.post("/mcp")
async def mcp_rpc(req: Request):
    payload = await req.json()
    # Basic JSON-RPC guardrails
    if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
        return JSONResponse({"jsonrpc":"2.0","id":payload.get("id"),
                             "error":{"code":-32600,"message":"Invalid Request"}}, status_code=400)

    method = payload.get("method")
    id_    = payload.get("id")
    params = payload.get("params") or {}

    # 1) REQUIRED MCP HANDSHAKE
    if method == "initialize":
        # You can tailor capabilities to what you actually support
        server_caps = {
            "tools": {"listChanged": True},         # server can send tools/list_changed notifications (optional)
            "resources": {"listChanged": True},     # ditto for resources (optional)
            # add other caps you truly support (prompts, sampling, logging, etc.)
        }
        server_info = {"name": "cv-server", "version": "0.1.0"}
        return mcp_response(id_, {
            "protocolVersion": MCP_PROTOCOL,
            "capabilities": server_caps,
            "serverInfo": server_info,
        })

    # 2) After initialize, normal MCP methods:
    if method == "tools/list":
        return mcp_response(id_, {
            "tools": [
                {
                    "name": "ask_cv",
                    "description": "Answer questions about the CV JSON",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"question": {"type":"string"}},
                        "required": ["question"],
                    },
                },
                {
                    "name": "send_email",
                    "description": "Send an email via SMTP",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "recipient":{"type":"string"},
                            "subject":{"type":"string"},
                            "body":{"type":"string"},
                        },
                        "required": ["recipient","subject","body"],
                    },
                },
            ]
        })

    if method == "tools/call":
        id_ = payload.get("id")
        params = payload.get("params") or {}
        name = params.get("name")
        args = params.get("arguments") or {}

        if not name:
            return mcp_response(id_, error={"code": -32602, "message": "Invalid params: missing 'name'"})

        try:
            if name == "ask_cv":
                # Import your existing tool implementation
                from server import mcp_server as mcp_mod
                ask_cv = mcp_mod.ask_cv

                # 1) If a typed input model exists, prefer it
                req = None
                AskCVInput = getattr(mcp_mod, "AskCVInput", None)
                if AskCVInput:
                    try:
                        req = AskCVInput(**args)  # e.g., {"question": "..."}
                    except Exception:
                        req = None

                # 2) Otherwise, provide dot-access (input.question)
                if req is None:
                    req = SimpleNamespace(**args)

                # 3) Call the tool; if it actually expects a string, try that too
                try:
                    result = ask_cv(req)
                except AttributeError:
                    result = ask_cv(args.get("question", ""))

                if inspect.isawaitable(result):
                    result = await result

                return mcp_response(id_, {"content": [{"type": "text", "text": str(result)}]})

            elif name == "send_email":
                # from server.emailer import send_email_smtp   (or wherever you implemented it)
                recipient = args.get("recipient")
                subject   = args.get("subject")
                body      = args.get("body")
                if not all([recipient, subject, body]):
                    return mcp_response(id_, error={"code": -32602, "message": "send_email requires recipient, subject, body"})

                ok = send_email_smtp(recipient, subject, body)  # or await if async
                msg = "Email sent." if ok else "Email failed."
                return mcp_response(id_, {
                    "content": [{"type": "text", "text": msg}]
                })

            else:
                return mcp_response(id_, error={"code": -32601, "message": f"Unknown tool: {name}"})

        except Exception as e:
            # Surface a tool error in MCP shape
            return mcp_response(id_, {
                "content": [{"type": "text", "text": f"Tool error: {e}"}],
                "isError": True
            })
    

    if method == "resources/list":
        # ... return your cv:json resource list ...
        ...

    if method == "resources/read":
        # ... return {"content":[{"type":"text","text": "<json or text>"}]}
        ...

    # Unknown method
    return mcp_response(id_, error={"code": -32601, "message": f"Unknown method: {method}"})


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
