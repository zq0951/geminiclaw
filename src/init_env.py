import os
import sys

def init_env(force=False):
    template_path = "SYSTEM_PROMPTS_TEMPLATE.md"
    if not os.path.exists(template_path):
        print(f"[Error] Template {template_path} not found.")
        return
    
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    parts = content.split("<!-- FILE: ")
    for part in parts:
        if not part.strip():
            continue
        
        # Extract filename and content
        lines = part.split("\n", 1)
        if len(lines) < 2:
            continue
            
        file_header = lines[0].strip()
        if not file_header.endswith("-->"):
            continue
            
        filename = file_header[:-3].strip()
        file_content = lines[1].lstrip('\n') # Clean leading newlines
        
        # Optional: remove trailing spaces/newlines that might have accumulated
        file_content = file_content.rstrip() + '\n'
            
        # Write to file if it doesn't exist OR if force is enabled
        if force or not os.path.exists(filename):
            action = "Overwriting" if os.path.exists(filename) else "Creating"
            print(f"[Init] {action} {filename}...")
            
            # Ensure directory exists for files like memory/heartbeat-state.json if added later
            os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
            
            with open(filename, "w", encoding="utf-8") as out:
                out.write(file_content)

if __name__ == "__main__":
    force_update = "--force" in sys.argv
    init_env(force=force_update)
