import os
import json
import logging
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GeminiEngine")

class GeminiCliAdapter:
    def __init__(self, executable_path="gemini"):
        self.session_id = None
        self.cmd_base = executable_path
        # When checking environment or cwd config
        self.cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # geminiclaw root

    def chat(self, prompt: str) -> dict:
        """Sends a prompt to the gemini CLI in headless mode."""
        
        # Build the command. 
        # -y : yolo mode to skip tool confirmations
        # -o json : enforce json output
        # -p : prompt
        cmd = [self.cmd_base, "-y", "-o", "json", "-p", prompt]
        
        # If we already have a session, resume it
        if self.session_id:
            cmd.extend(["-r", self.session_id])
            
        logger.info(f"Executing gemini cli. Session ID: {self.session_id or 'NEW'}")
        
        try:
            result = subprocess.run(
                cmd, 
                cwd=self.cwd,
                capture_output=True, 
                text=True, 
                check=True,
                stdin=subprocess.DEVNULL
            )
            output = result.stdout.strip()
            
            try:
                data = json.loads(output)
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from CLI output.")
                return {"error": "JSON parse error", "raw": output}
                
            # The exact JSON structure returned by gemini CLI might vary (e.g., depends on gemini configuration)
            # Typically if using resuming, the gemini cli might echo back the session it used, or we might need 
            # to parse it carefully if the CLI itself manages sessions. 
            # Assuming the CLI returns a "session_id" or "session" key for new chats:
            if not self.session_id:
                if "session" in data:
                    self.session_id = data["session"]
                elif "session_id" in data:
                    self.session_id = data["session_id"]
                
                if self.session_id:
                    logger.info(f"Captured new Session ID: {self.session_id}")
            
            return data
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Gemini CLI error (return code {e.returncode}):\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
            return {"error": "subprocess failed", "stdout": e.stdout, "stderr": e.stderr}

if __name__ == "__main__":
    adapter = GeminiCliAdapter()
    print("Testing initial connection and context loading...")
    # This simple prompt will trigger GEMINI.md reading
    res = adapter.chat("Please summarize the identity and goals specified in your current directory context. (Respond purely in text)")
    print(json.dumps(res, indent=2, ensure_ascii=False))
