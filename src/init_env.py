import os

def init_env():
    template_path = "SYSTEM_PROMPTS_TEMPLATE.md"
    if not os.path.exists(template_path):
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
        file_content = lines[1]
        
        # Optional: remove trailing newlines that might have accumulated
        while file_content.endswith('\n\n'):
            file_content = file_content[:-1]
            
        # Write to file if it doesn't exist
        if not os.path.exists(filename):
            print(f"[Init] Creating {filename} from template...")
            with open(filename, "w", encoding="utf-8") as out:
                out.write(file_content)

if __name__ == "__main__":
    init_env()
