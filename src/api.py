import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks, Depends, HTTPException, Header, status
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from engine import GeminiCliAdapter

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

def get_access_code():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("access_code", "claw")
            except:
                pass
    else:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"access_code": "claw"}, f, indent=2)
    return "claw"

app = FastAPI(title="Gemini-Claw Control Panel")
engine = GeminiCliAdapter()

import hmac
import time
import secrets
SECRET_KEY = secrets.token_hex(32)

def create_token():
    exp = int(time.time()) + 24 * 3600
    exp_bytes = str(exp).encode("utf-8")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), exp_bytes, "sha256").hexdigest()
    return f"{exp}.{sig}"

def is_valid_token(token: str):
    if not token or "." not in token:
        return False
    try:
        exp_str, sig = token.split(".", 1)
        if int(time.time()) > int(exp_str):
            return False
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), exp_str.encode("utf-8"), "sha256").hexdigest()
        return hmac.compare_digest(sig, expected_sig)
    except Exception:
        return False

# Serve static files for the frontend Dashboard
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(ROOT_DIR, "web", "dist")
# 修改为根目录下的 media 文件夹，完全解耦
MEDIA_DIR = os.path.join(ROOT_DIR, "media")

# 确保媒体目录存在
os.makedirs(MEDIA_DIR, exist_ok=True)

# 映射媒体文件路径，实现即时访问
app.mount("/media", StaticFiles(directory=MEDIA_DIR), name="media")

if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Frontend not built yet.</h1><p>Please run 'npm run build' in the web directory.</p>")

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "session_id": engine.session_id}

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    if not is_valid_token(token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return token

@app.post("/api/v1/auth/login")
async def login(request: Request):
    import hashlib
    data = await request.json()
    password_hash = data.get("password", "")
    # 默认值: 'claw' 对应的 MD5
    # 我们从项目根目录的 config.json 进行读取
    expected_raw = get_access_code()
    expected_hash = hashlib.md5(expected_raw.encode("utf-8")).hexdigest()
    
    if password_hash == expected_hash:
        return {"status": "ok", "token": create_token()}
    from fastapi import HTTPException
    raise HTTPException(status_code=401, detail="访问密钥无效 (Invalid Access Code)")

@app.get("/api/v1/sessions", dependencies=[Depends(verify_token)])
async def list_sessions():
    """List all available sessions."""
    sessions = await asyncio.to_thread(engine.get_sessions)
    return {"sessions": sessions, "current_session_id": engine.session_id}

@app.post("/api/v1/sessions/switch", dependencies=[Depends(verify_token)])
async def switch_session(request: Request):
    """Switch to a specific session."""
    data = await request.json()
    session_id = data.get("session_id")
    if not session_id:
        return {"error": "session_id is required"}
    
    engine.set_session(session_id)
    return {"status": "ok", "session_id": engine.session_id}

@app.get("/api/v1/sessions/history", dependencies=[Depends(verify_token)])
async def get_session_history(session_id: str = None):
    """Get history for a specific session."""
    sid = session_id or engine.session_id
    if not sid:
        return {"history": []}
    history = await asyncio.to_thread(engine.get_session_history, sid)
    return {"history": history}

@app.post("/api/v1/chat", dependencies=[Depends(verify_token)])
async def send_chat(request: Request):
    """Event Stream JSONL endpoint triggered from frontend."""
    data = await request.json()
    prompt = data.get("prompt", "")
    
    if not prompt:
        return {"error": "Prompt cannot be empty"}
        
    if prompt.strip() == "/new":
        engine.reset_session()
        # Ensure we return SSE format for compatibility if client expects it
        async def mock_event():
            yield f"data: {json.dumps({'type': 'init', 'session_id': None})}\n\n"
            yield f"data: {json.dumps({'type': 'message', 'role': 'assistant', 'content': '开启了全新的会话！'})}\n\n"
        return StreamingResponse(mock_event(), media_type="text/event-stream")

    # Delegate to the engine's stream generator without blocking the main event loop
    async def event_generator():
        async for event in engine.chat_stream(prompt):
            yield f"data: {json.dumps(event)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.get("/api/v1/skills", dependencies=[Depends(verify_token)])
async def list_skills():
    """List all available skills in the skills directory."""
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
    skills = []
    if os.path.exists(skills_dir):
        for file in os.listdir(skills_dir):
            if file.endswith(".py") and file != "loader.py":
                skills.append(file)
    return {"skills": sorted(skills)}

@app.get("/api/v1/skills/{skill_name}", dependencies=[Depends(verify_token)])
async def get_skill(skill_name: str):
    """Read the content of a specific skill."""
    skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
    file_path = os.path.join(skills_dir, skill_name)
    if not os.path.exists(file_path):
        return {"error": "Skill not found"}
    with open(file_path, "r", encoding="utf-8") as f:
        return {"name": skill_name, "content": f.read()}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time dashboard events and manual overriding."""
    await websocket.accept()
    
    token = websocket.query_params.get("token")
    if not is_valid_token(token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await websocket.send_text("Connected to Gemini-Claw.")
    try:
        while True:
            data = await websocket.receive_text()
            # Simple ping-pong or command execution through WS
            if data.startswith("/"):
                command = data[1:]
                await websocket.send_text(f"> 正在执行系统级别指令: {command}")
                # Stream the outputs directly
                async for event in engine.chat_stream(f"用户在控制台下发了直接命令: {command}"):
                    await websocket.send_text(json.dumps(event, ensure_ascii=False))
            else:
                await websocket.send_text("> 收到普通消息，暂不调用模型。使用 / 作为指令开头。")
                
    except Exception as e:
        print(f"WebSocket Error: {e}")
        pass

if __name__ == "__main__":
    import uvicorn
    # Optional wrapper to start locally
    uvicorn.run("api:app", host="0.0.0.0", port=8888, reload=True)
