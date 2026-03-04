import os
import json
import logging
import asyncio
import datetime
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GeminiEngine")

class GeminiCliAdapter:
    def __init__(self, executable_path="gemini"):
        import shutil
        self.cmd_base = shutil.which(executable_path) or executable_path
        self.cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # geminiclaw root
        self.session_id = None
        self.session_file = os.path.join(self.cwd, ".current_session")
        self.history_dir = os.path.join(self.cwd, ".history")
        os.makedirs(self.history_dir, exist_ok=True)
        self._load_session()

    def _load_session(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    self.session_id = f.read().strip()
                logger.info(f"Loaded session ID from file: {self.session_id}")
            except Exception as e:
                logger.error(f"Failed to load session file: {e}")
        
    def _add_to_tracked_sessions(self, sid):
        tracked_file = os.path.join(self.cwd, ".tracked_sessions")
        tracked = set()
        if os.path.exists(tracked_file):
            try:
                with open(tracked_file, "r") as f:
                    tracked = set(f.read().splitlines())
            except Exception:
                pass
        if sid not in tracked:
            tracked.add(sid)
            try:
                with open(tracked_file, "w") as f:
                    f.write("\n".join(tracked))
            except Exception:
                pass

    def _save_session(self, sid):
        self.session_id = sid
        try:
            with open(self.session_file, "w") as f:
                f.write(sid)
            self._add_to_tracked_sessions(sid)
        except Exception as e:
            logger.error(f"Failed to save session file: {e}")

    def reset_session(self):
        self.session_id = None
        if os.path.exists(self.session_file):
            os.remove(self.session_file)
        logger.info("Session reset.")

    def set_session(self, sid):
        self._save_session(sid)
        logger.info(f"Session manually set to {sid}")

    async def chat_stream(self, prompt: str, model: str = None):
        """Sends a prompt to the gemini CLI and yields JSONL events."""
        cmd = [self.cmd_base, "-y", "-o", "stream-json", "-p", prompt]
        
        if model:
            cmd.extend(["-m", model])

        
        if self.session_id:
            cmd.extend(["-r", self.session_id])
            
        logger.info(f"Executing gemini cli (stream). Session ID: {self.session_id or 'NEW'}")
        # 使用独立的系统线程来规避 Windows 环境下各类基于 SelectorEventLoop 引发的 RuntimeError
        process = subprocess.Popen(
            cmd,
            cwd=self.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL
        )

        full_response_text = ""
        
        try:
            while True:
                line = await asyncio.to_thread(process.stdout.readline)
                if not line:
                    break
                
                line_text = line.decode('utf-8').strip()
                if not line_text:
                    continue
                
                try:
                    event = json.loads(line_text)
                    
                    if event.get("type") == "init":
                        sid = event.get("session_id")
                        if sid:
                            self._save_session(sid)
                    elif event.get("type") == "message" and event.get("role") == "assistant" and "content" in event:
                        full_response_text += event["content"]
                            
                    yield event
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSONL line: {line_text}")
            
            stderr_output = await asyncio.to_thread(process.stderr.read)
            await asyncio.to_thread(process.wait)
            
            if process.returncode != 0:
                err_text = stderr_output.decode('utf-8', errors='replace')
                logger.error(f"CLI Error: {err_text}")
                yield {"type": "error", "message": "Subprocess error", "details": err_text}
                
            if full_response_text:
                self._log_interaction(prompt, {"response": full_response_text})
                self._append_history(self.session_id, prompt, full_response_text)
                
        except Exception as e:
            logger.error(f"Error during stream processing: {e}")
            yield {"type": "error", "message": str(e)}

    def chat(self, prompt: str, model: str = None) -> dict:
        """Sends a prompt to the gemini CLI in headless mode synchronously. Used by cron and legacy."""
        cmd = [self.cmd_base, "-y", "-o", "json", "-p", prompt]
        if model:
            cmd.extend(["-m", model])
        if self.session_id:
            cmd.extend(["-r", self.session_id])
            
        logger.info(f"Executing gemini cli (sync). Session ID: {self.session_id or 'NEW'}")
        try:
            result = subprocess.run(
                cmd, 
                cwd=self.cwd,
                capture_output=True, 
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                stdin=subprocess.DEVNULL
            )
            output = result.stdout.strip()
            
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                return {"error": "JSON parse error", "raw": output}
                
            if not self.session_id:
                if "session" in data:
                    self._save_session(data["session"])
                elif "session_id" in data:
                    self._save_session(data["session_id"])
                    
            self._log_interaction(prompt, data)
            resp_text = str(data)
            if isinstance(data, dict):
                resp_text = data.get("response", json.dumps(data, ensure_ascii=False))
            self._append_history(self.session_id, prompt, resp_text)
            
            return data
            
        except subprocess.CalledProcessError as e:
            return {"error": "subprocess failed", "stdout": e.stdout, "stderr": e.stderr}

    def get_sessions(self):
        """Returns the list of available sessions by calling gemini --list-sessions -o json"""
        tracked_file = os.path.join(self.cwd, ".tracked_sessions")
        tracked = set()
        if os.path.exists(tracked_file):
            try:
                with open(tracked_file, "r") as f:
                    tracked = set(f.read().splitlines())
            except Exception:
                pass

        try:
            result = subprocess.run([self.cmd_base, "--list-sessions", "-o", "json"], cwd=self.cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            lines = result.stdout.strip().split("\n")
            sessions = []
            for line in lines:
                if "[" in line and "]" in line:
                    parts = line.split("[")
                    if len(parts) > 1:
                        sid_part = parts[-1].split("]")[0]
                        desc_part = parts[0].strip()
                        if sid_part in tracked:
                            sessions.append({"id": sid_part, "desc": desc_part})
            return sessions
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []

    def _log_interaction(self, prompt, response_data):
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            log_dir = os.path.join(self.cwd, "memory")
            os.makedirs(log_dir, exist_ok=True)
            log_path = os.path.join(log_dir, f"{today}.md")
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            resp_str = json.dumps(response_data, ensure_ascii=False)
            if isinstance(response_data, dict) and "response" in response_data:
                resp_str = response_data["response"]

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n### [{timestamp}] Interaction\n")
                f.write(f"**Prompt**: {prompt}\n\n")
                f.write(f"**Response**:\n{resp_str}\n\n---\n")
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")

    def _get_safe_history_path(self, sid):
        if not sid: return None
        import re
        safe_sid = re.sub(r'[\\/:*?"<>|]', '_', sid)
        return os.path.join(self.history_dir, f"{safe_sid}.json")

    def _append_history(self, sid, prompt, response):
        history_file = self._get_safe_history_path(sid)
        if not history_file: return
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": response})
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")

    def get_session_history(self, sid):
        history_file = self._get_safe_history_path(sid)
        if not history_file: return []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

