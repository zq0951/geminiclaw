import sqlite3
import datetime
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                importance INTEGER DEFAULT 1,
                timestamp TEXT NOT NULL,
                category TEXT DEFAULT 'general'
            )
        """)
        conn.commit()

def add_memory(content: str, importance: int = 1, category: str = "general"):
    """Adds a generic memory fact to the long term SQLite database."""
    timestamp = datetime.datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO memories (content, importance, timestamp, category) VALUES (?, ?, ?, ?)",
            (content, importance, timestamp, category)
        )
        conn.commit()
    return {"status": "success", "message": "Memory saved."}

def search_memory(query: str, limit: int = 5):
    """Simple keyword search. An agent could also execute a SQL query via system calls if allowed."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Very crude LIKE search
        cursor.execute(
            "SELECT id, content, importance, timestamp, category FROM memories WHERE content LIKE ? ORDER BY importance DESC, timestamp DESC LIMIT ?", 
            (f"%{query}%", limit)
        )
        results = cursor.fetchall()
        
    return [
        {"id": r[0], "content": r[1], "importance": r[2], "timestamp": r[3], "category": r[4]}
        for r in results
    ]

if __name__ == "__main__":
    init_db()
    
    # Simple CLI argument handler so the agent can invoke this file natively
    import argparse
    parser = argparse.ArgumentParser(description="Memory Management")
    subparsers = parser.add_subparsers(dest="action")
    
    parser_add = subparsers.add_parser("add")
    parser_add.add_argument("content", type=str)
    parser_add.add_argument("--importance", type=int, default=1)
    parser_add.add_argument("--category", type=str, default="general")
    
    parser_search = subparsers.add_parser("search")
    parser_search.add_argument("query", type=str)
    
    args = parser.parse_args()
    if args.action == "add":
        print(add_memory(args.content, args.importance, args.category))
    elif args.action == "search":
        import json
        print(json.dumps(search_memory(args.query), ensure_ascii=False, indent=2))
    else:
        print("Usage: python memory.py [add|search] ...")
