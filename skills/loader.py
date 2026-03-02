#!/usr/bin/env python3
import os
import ast
import json

SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_MD_PATH = os.path.join(os.path.dirname(SKILLS_DIR), "TOOLS.md")

def extract_meta(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
            
        # extract top level docstring
        docstring = ast.get_docstring(tree)
        if not docstring:
            # find first function docstring
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        break
        return docstring or "No description provided."
    except Exception as e:
        return f"Error parsing: {str(e)}"

def update_tools_md():
    tools = []
    for file in os.listdir(SKILLS_DIR):
        if file.endswith(".py") and file != "loader.py":
            desc = extract_meta(os.path.join(SKILLS_DIR, file))
            tools.append({
                "script": file,
                "description": desc.split('\n')[0]
            })
            
    content = """# ==============================================================================
# 💡 TOOLS: 技能能力库概览
# ==============================================================================
这个文档描述了 `skills/` 目录下存放的扩展能力脚本。

### 目录指引与描述
"""
    for idx, t in enumerate(tools, 1):
        content += f"\n{idx}. **(`{t['script']}`)**: {t['description']}"
        
    with open(TOOLS_MD_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"TOOLS.md updated successfully with {len(tools)} tools.")
    
if __name__ == "__main__":
    update_tools_md()
