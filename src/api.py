import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from engine import GeminiCliAdapter

app = FastAPI(title="Gemini-Claw Control Panel")
engine = GeminiCliAdapter()

# Serve static files for the frontend Dashboard
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        with open(os.path.join(STATIC_DIR, "index.html"), "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "session_id": engine.session_id}

@app.post("/api/v1/chat")
async def send_chat(request: Request):
    """Synchronous REST API chat endpoint triggered from frontend."""
    data = await request.json()
    prompt = data.get("prompt", "")
    
    if not prompt:
        return {"error": "Prompt cannot be empty"}
        
    # Delegate to the engine (Note: For long running commands, subprocess block shouldn't block main event loop. This is acceptable for MVP.)
    result = engine.chat(prompt)
    return {"result": result, "session_id": engine.session_id}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time dashboard events and manual overriding."""
    await websocket.accept()
    await websocket.send_text("Connected to Gemini-Claw.")
    try:
        while True:
            data = await websocket.receive_text()
            # Simple ping-pong or command execution through WS
            if data.startswith("/"):
                command = data[1:]
                await websocket.send_text(f"> 正在执行系统级别指令: {command}")
                # For safety, pass to engine to process it rather than evaluating code directly
                res = engine.chat(f"用户在控制台下发了直接命令: {command}")
                await websocket.send_text(json.dumps(res, indent=2, ensure_ascii=False))
            else:
                await websocket.send_text("> 收到普通消息，暂不调用模型。使用 / 作为指令开头。")
                
    except Exception as e:
        print(f"WebSocket Error: {e}")
        pass

if __name__ == "__main__":
    import uvicorn
    # Optional wrapper to start locally
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
