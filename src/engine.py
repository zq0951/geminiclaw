import os
import json
import logging
import asyncio
import datetime
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GeminiEngine")

class GeminiCliAdapter:
    def __init__(self, executable_path="/root/.nvm/versions/node/v24.12.0/bin/node /root/.nvm/versions/node/v24.12.0/bin/gemini"):
        import shutil
        self.cmd_base = executable_path.split() # 转换为列表以方便 subprocess 使用
        self.cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # geminiclaw root
        self.session_id = None
        self.session_file = os.path.join(self.cwd, ".current_session")
        self.history_dir = os.path.join(self.cwd, ".history")
        self.lock_file = os.path.join(self.cwd, ".geminiclaw.lock")
        self.rate_limit_lock_file = os.path.join(self.cwd, ".rate_limit_lock")
        os.makedirs(self.history_dir, exist_ok=True)
        self._load_session()

    def is_rate_limited(self):
        if os.path.exists(self.rate_limit_lock_file):
            try:
                with open(self.rate_limit_lock_file, "r") as f:
                    content = f.read().strip()
                    try:
                        lock_timestamp = float(content)
                    except ValueError:
                        # Fallback for old date-based format
                        os.remove(self.rate_limit_lock_file)
                        return False
                
                # Check if 1 hour (3600 seconds) has passed
                if datetime.datetime.now().timestamp() - lock_timestamp < 3600:
                    return True
                else:
                    os.remove(self.rate_limit_lock_file)
                    logger.info("Rate limit lock (1h) expired and removed.")
            except Exception as e:
                logger.error(f"Failed to check rate limit lock: {e}")
        return False

    def mark_rate_limited(self):
        now = datetime.datetime.now().timestamp()
        try:
            with open(self.rate_limit_lock_file, "w") as f:
                f.write(str(now))
            logger.warning("Rate limit (429) detected. System locked for 1 hour.")
        except Exception as e:
            logger.error(f"Failed to create rate limit lock: {e}")

    def _load_session(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r") as f:
                    self.session_id = f.read().strip()
            except Exception as e:
                logger.error(f"Failed to load session file: {e}")
        else:
            self.session_id = None
        
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

    def _acquire_lock_sync(self):
        import fcntl, time
        fd = open(self.lock_file, "w")
        logger.info("Waiting for engine lock...")
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.info("Engine lock acquired.")
                return fd
            except BlockingIOError:
                time.sleep(1)

    async def _acquire_lock_async(self):
        import fcntl
        fd = open(self.lock_file, "w")
        logger.info("Waiting for engine lock (async)...")
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                logger.info("Engine lock acquired.")
                return fd
            except BlockingIOError:
                await asyncio.sleep(1)

    def _release_lock(self, fd):
        if fd:
            import fcntl
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
                fd.close()
                logger.info("Engine lock released.")
            except Exception:
                pass

    async def chat_stream(self, prompt: str, model: str = None):
        """Sends a prompt to the gemini CLI and yields JSONL events."""
        lock_fd = await self._acquire_lock_async()
        if self.is_rate_limited():
            logger.warning("System is currently rate-limited (429). Skipping chat_stream.")
            self._release_lock(lock_fd)
            yield {"type": "error", "message": "System is rate-limited. Please retry later."}
            return
        self._load_session()
        cmd = self.cmd_base + ["-y", "-o", "stream-json", "-p", prompt]
        
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
        last_saved_len = 0
        is_first_save = True
        backgrounded = False
        
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
                        
                        # 增量保存：每增加约 50 个字符保存一次记录，防止断开时数据丢失
                        if len(full_response_text) - last_saved_len > 50:
                            self._update_history_incremental(self.session_id, prompt, full_response_text, is_first_save)
                            is_first_save = False
                            last_saved_len = len(full_response_text)
                            
                    yield event
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSONL line: {line_text}")
            
            stderr_output = await asyncio.to_thread(process.stderr.read)
            await asyncio.to_thread(process.wait)
            
            if process.returncode != 0:
                err_text = stderr_output.decode('utf-8', errors='replace')
                logger.error(f"CLI Error: {err_text}")
                if "429" in err_text or "Quota exceeded" in err_text or "RESOURCE_EXHAUSTED" in err_text:
                    self.mark_rate_limited()
                yield {"type": "error", "message": "Subprocess error", "details": err_text}
                
        except asyncio.CancelledError:
            logger.warning("Streaming connection was cancelled by the client. Continuing in background to finish response...")
            backgrounded = True
            
            async def run_to_completion(proc, p_prompt, session_id, p_first_save, p_text, p_last_len):
                try:
                    while True:
                        l = await asyncio.to_thread(proc.stdout.readline)
                        if not l:
                            break
                        l_text = l.decode('utf-8').strip()
                        if not l_text: continue
                        try:
                            ev = json.loads(l_text)
                            if ev.get("type") == "message" and ev.get("role") == "assistant" and "content" in ev:
                                p_text += ev["content"]
                                if len(p_text) - p_last_len > 50:
                                    self._update_history_incremental(session_id, p_prompt, p_text, p_first_save)
                                    p_first_save = False
                                    p_last_len = len(p_text)
                        except json.JSONDecodeError:
                            pass
                    await asyncio.to_thread(proc.wait)
                except Exception as e:
                    logger.error(f"Error in background generation: {e}")
                finally:
                    if p_text:
                        self._update_history_incremental(session_id, p_prompt, p_text, p_first_save)
                        self._log_interaction(p_prompt, {"response": p_text})
                    self._release_lock(lock_fd)
            
            asyncio.create_task(run_to_completion(
                process, prompt, self.session_id, is_first_save, full_response_text, last_saved_len
            ))
            raise
        except Exception as e:
            logger.error(f"Error during stream processing: {e}")
            yield {"type": "error", "message": str(e)}
        finally:
            if not backgrounded:
                if full_response_text:
                    # 最终检查并保存
                    self._update_history_incremental(self.session_id, prompt, full_response_text, is_first_save)
                    # markdown 日志也保留在最后统一写入
                    self._log_interaction(prompt, {"response": full_response_text})
                self._release_lock(lock_fd)

    def chat(self, prompt: str, model: str = None) -> dict:
        """Sends a prompt to the gemini CLI in headless mode synchronously. Used by cron and legacy."""
        lock_fd = self._acquire_lock_sync()
        if self.is_rate_limited():
            logger.warning("System is currently rate-limited (429). Skipping chat.")
            self._release_lock(lock_fd)
            return {"error": "rate_limited", "message": "System is rate-limited. Please retry later."}
        try:
            self._load_session()
            cmd = self.cmd_base + ["-y", "-o", "json", "-p", prompt]
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
                
                def extract_json_blocks(text):
                    blocks = []
                    depth = 0
                    start = -1
                    for i, c in enumerate(text):
                        if c == '{':
                            if depth == 0:
                                start = i
                            depth += 1
                        elif c == '}':
                            depth -= 1
                            if depth == 0 and start != -1:
                                blocks.append(text[start:i+1])
                    return blocks

                try:
                    all_blocks = extract_json_blocks(output)
                    if all_blocks:
                        data = None
                        for block in reversed(all_blocks):
                            try:
                                data = json.loads(block)
                                break
                            except:
                                continue
                        if not data:
                            raise json.JSONDecodeError("No valid JSON found in all blocks", output, 0)
                    else:
                        data = json.loads(output)
                except json.JSONDecodeError:
                    logger.error(f"JSON parse error. Raw output: {output}")
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
                err_text = e.stderr or ""
                if "429" in err_text or "Quota exceeded" in err_text or "RESOURCE_EXHAUSTED" in err_text:
                    self.mark_rate_limited()
                return {"error": "subprocess failed", "stdout": e.stdout, "stderr": e.stderr}
        finally:
            self._release_lock(lock_fd)

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
            result = subprocess.run(self.cmd_base + ["--list-sessions", "-o", "json"], cwd=self.cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
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

    def _update_history_incremental(self, sid, prompt, response, is_first: bool):
        history_file = self._get_safe_history_path(sid)
        if not history_file: return
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass
        
        if is_first:
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": response})
        else:
            if history and history[-1].get("role") == "assistant":
                history[-1]["content"] = response
            else:
                history.append({"role": "user", "content": prompt})
                history.append({"role": "assistant", "content": response})
                
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history incrementally: {e}")

    def _append_history(self, sid, prompt, response):
        self._update_history_incremental(sid, prompt, response, is_first=True)

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

