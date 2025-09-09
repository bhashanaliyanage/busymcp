# MCP CV Server + Playground

This project implements a **Model Context Protocol (MCP) server** that can:

- **Chat about my CV** → answers questions like *“What role did I have at my last position?”*  
- **Send email notifications** → exposes a `send_email` tool with recipient, subject, and body.  
- **Expose resources** → provides `cv:json` resource so clients can inspect the structured resume data.  

Also, a **Next.js playground** is included to demo:

- Asking CV questions through a simple web chat  
- Sending test emails through the MCP server  

---

## Tech Stack

- **Backend (MCP server):** FastAPI, MCP Python SDK, Uvicorn  
- **Frontend:** Next.js
- **Email integration:** SMTP (tested with Gmail App Password)

---

## Endpoints

- `GET /healthz` → Health check  
- `POST /chat` → Ask a question about the CV  
- `POST /email/send` → Send an email  
- `GET /mcp` → MCP server endpoint (HTTP Stream transport)  

---

## Example Usage

### Chat

```http
POST /chat
Content-Type: application/json

{
  "question": "What role did I have at my last position?"
}
```

Response:

```json
{
  "answer": "Software Engineer at CeyMusic Publishing, Sri Lanka (Oct 2023 – Present)."
}
```

### Send Email

```http
POST /email/send
Content-Type: application/json

{
  "recipient": "test@example.com",
  "subject": "Hello from MCP",
  "body": "This is a test email from the MCP server."
}
```

---

## Running Locally

### Requirements

- Python 3.10 or later

### Backend Setup

1. **Create a virtual environment (Python 3.10+):**

   ```bash
   python3.10 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run the server:**

   ```bash
   uvicorn server.app:app --reload --port 8000
   ```

### Frontend Setup (optional)

1. **Create a local environment file:**
   - Inside the `web` folder, create a file named `.env.local` and add:

     ```bash
     NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
     ```

2. **Install and run:**

   ```bash
   cd web
   npm install
   npm run dev
   ```

Visit: [http://localhost:3000](http://localhost:3000)
