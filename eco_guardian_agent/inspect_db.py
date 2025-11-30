import sqlite3
from pathlib import Path
import json

def check_data_in_db():
    # Auto-resolve DB path relative to this script
    db_path = Path(__file__).parent / "ecoguardian_sessions.db"
    print(f"📁 Using DB: {db_path}\n")

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # -----------------------------
        # List all tables
        # -----------------------------
        print("=== TABLES ===")
        tables = cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        for t in tables:
            print(" -", t["name"])

        # -----------------------------
        # Show schema of events table
        # -----------------------------
        print("\n=== EVENTS SCHEMA ===")
        schema = cur.execute("PRAGMA table_info(events)").fetchall()
        for col in schema:
            print(col)

        # -----------------------------
        # Read latest 50 events
        # -----------------------------
        print("\n=== EVENTS (latest 50) ===")

        query = """
        SELECT
            id,
            app_name,
            user_id,
            session_id,
            invocation_id,
            author,
            timestamp,
            content,
            error_code,
            error_message
        FROM events
        ORDER BY timestamp DESC
        LIMIT 50
        """

        rows = cur.execute(query).fetchall()

        print("\nColumns:", rows[0].keys() if rows else [])
        print("\n--- DATA ---")
        for row in rows:
            # Pretty-print long JSON-like `content` if needed
            content = row["content"]
            try:
                content_parsed = json.loads(content)
                content = json.dumps(content_parsed, indent=2)
            except:
                pass

            print(
                f"\n----- EVENT -----\n"
                f"ID: {row['id']}\n"
                f"App: {row['app_name']}\n"
                f"User: {row['user_id']}\n"
                f"Session: {row['session_id']}\n"
                f"Invocation: {row['invocation_id']}\n"
                f"Author: {row['author']}\n"
                f"Timestamp: {row['timestamp']}\n"
                f"Error Code: {row['error_code']}\n"
                f"Error Message: {row['error_message']}\n"
                f"Content:\n{content}\n"
            )

def inspect_schema():
    db_path = Path(__file__).parent / "ecoguardian_sessions.db"
    print("📁 DB:", db_path)

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        print("\n=== SCHEMA FOR events ===")
        schema = cur.execute(
            "PRAGMA table_info(events)"
        ).fetchall()

        for col in schema:
            print(col)



if __name__ == "__main__":
    check_data_in_db()
