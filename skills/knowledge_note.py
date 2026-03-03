#!/usr/bin/env python3
"""
深度研究与知识笔记 (Save/Read Knowledge Notes).
Parameters:
  --action: 'save' or 'read'
  --topic: The topic of the note
  --content: (For 'save') The markdown content
  --tags: (For 'save', optional) Comma-separated tags
"""
import os
import json
import argparse
from datetime import datetime

# Define knowledge directory inside geminiclaw
KNOWLEDGE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "memory", "knowledge"
)

def ensure_dir():
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)

def save_note(topic: str, content: str, tags: list):
    ensure_dir()
    try:
        filename = f"{topic.replace(' ', '_').lower()}.md"
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        full_content = f"---\n"
        full_content += f"topic: {topic}\n"
        full_content += f"tags: {json.dumps(tags, ensure_ascii=False)}\n"
        full_content += f"updated: {time_str}\n"
        full_content += f"---\n\n{content}"
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)
            
        return {"status": "success", "message": f"Successfully saved knowledge note: {topic} at {filepath}"}
    except Exception as e:
        return {"error": str(e), "message": "Failed to save note."}

def read_note(topic: str):
    ensure_dir()
    try:
        filename = f"{topic.replace(' ', '_').lower()}.md"
        filepath = os.path.join(KNOWLEDGE_DIR, filename)
        
        if not os.path.exists(filepath):
            # Try fuzzy matching
            matched = False
            for f in os.listdir(KNOWLEDGE_DIR):
                if topic.lower() in f.lower():
                    filepath = os.path.join(KNOWLEDGE_DIR, f)
                    matched = True
                    break
                    
            if not matched:
                return {"status": "not_found", "message": f"No knowledge note found for topic: {topic}"}
                
        with open(filepath, "r", encoding="utf-8") as f:
            return {"status": "success", "topic": topic, "content": f.read()}
    except Exception as e:
        return {"error": str(e), "message": "Failed to read note."}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save or Read Knowledge Notes.")
    parser.add_argument("--action", type=str, required=True, choices=["save", "read"], help="Action to perform.")
    parser.add_argument("--topic", type=str, required=True, help="Topic of the note.")
    parser.add_argument("--content", type=str, default="", help="Content of the note (Markdown format).")
    parser.add_argument("--tags", type=str, default="", help="Comma separated tags.")
    
    args = parser.parse_args()
    
    if args.action == "save":
        if not args.content:
            result = {"error": "Content is required for saving."}
        else:
            tags_list = [t.strip() for t in args.tags.split(",") if t.strip()]
            result = save_note(args.topic, args.content, tags_list)
    else:
        result = read_note(args.topic)
        
    print(json.dumps(result, indent=2, ensure_ascii=False))
