"""
monitoring.py — Log setiap query ke SQLite dan tampilkan stats di Streamlit.
Tidak ada dependency eksternal selain standard library Python.
"""

import json
import sqlite3
from collections import Counter
from datetime import datetime

DB_FILE = "monitoring.db"
MODEL_NAME = "gemini-2.5-flash-lite"

# Harga Gemini 2.5 Flash Lite (USD per 1 juta token)
INPUT_TOKEN_PRICE = 0.10
OUTPUT_TOKEN_PRICE = 0.40


# ─── Init ─────────────────────────────────────────────────────────────────────

def init_db() -> None:
    """Buat monitoring.db dan tabel query_logs kalau belum ada."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT,
                query           TEXT,
                response_time   REAL,
                input_tokens    INTEGER,
                output_tokens   INTEGER,
                total_tokens    INTEGER,
                estimated_cost  REAL,
                sources         TEXT,
                is_fallback     INTEGER,
                model_name      TEXT
            )
        """)
        conn.commit()


# ─── Log ──────────────────────────────────────────────────────────────────────

def log_query(query: str, result: dict, formatted_sources: list[str]) -> None:
    """Simpan satu baris log. result adalah dict return dari ask() di llm.py."""
    input_tokens = result.get("input_tokens", 0)
    output_tokens = result.get("output_tokens", 0)
    estimated_cost = (
        input_tokens * INPUT_TOKEN_PRICE + output_tokens * OUTPUT_TOKEN_PRICE
    ) / 1_000_000

    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            """
            INSERT INTO query_logs
                (timestamp, query, response_time, input_tokens, output_tokens,
                 total_tokens, estimated_cost, sources, is_fallback, model_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                query,
                result.get("response_time", 0.0),
                input_tokens,
                output_tokens,
                result.get("tokens", 0),
                estimated_cost,
                json.dumps(formatted_sources, ensure_ascii=False),
                1 if result.get("is_fallback") else 0,
                MODEL_NAME,
            ),
        )
        conn.commit()


# ─── Stats ────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """Agregasi dari seluruh query_logs. Siap ditampilkan di Streamlit."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("""
            SELECT
                COUNT(*)                        AS query_count,
                AVG(response_time)              AS avg_response_time,
                SUM(total_tokens)               AS total_tokens,
                SUM(estimated_cost)             AS total_cost_usd,
                AVG(is_fallback) * 100          AS fallback_rate
            FROM query_logs
        """).fetchone()

        query_count = row["query_count"] or 0
        avg_rt = round(row["avg_response_time"] or 0.0, 2)
        total_tokens = row["total_tokens"] or 0
        total_cost = round(row["total_cost_usd"] or 0.0, 6)
        fallback_rate = round(row["fallback_rate"] or 0.0, 1)

        # Most referenced source — flatten semua JSON arrays dari kolom sources
        sources_rows = conn.execute("SELECT sources FROM query_logs WHERE sources IS NOT NULL").fetchall()

    all_sources: list[str] = []
    for r in sources_rows:
        try:
            parsed = json.loads(r["sources"])
            if isinstance(parsed, list):
                all_sources.extend(parsed)
        except (json.JSONDecodeError, TypeError):
            pass

    if all_sources:
        most_common, _ = Counter(all_sources).most_common(1)[0]
    else:
        most_common = "—"

    return {
        "query_count": query_count,
        "avg_response_time": avg_rt,
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "fallback_rate": fallback_rate,
        "most_referenced_source": most_common,
    }


# ─── Recent Logs ──────────────────────────────────────────────────────────────

def get_recent_logs(n: int = 10) -> list[dict]:
    """Return n query terbaru, ordered by timestamp DESC."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT timestamp, query, response_time, total_tokens, estimated_cost, is_fallback
            FROM query_logs
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (n,),
        ).fetchall()

    result = []
    for row in rows:
        query_text = row["query"] or ""
        if len(query_text) > 60:
            query_text = query_text[:60] + "..."
        result.append({
            "timestamp": row["timestamp"],
            "query": query_text,
            "response_time": row["response_time"],
            "total_tokens": row["total_tokens"],
            "estimated_cost": row["estimated_cost"],
            "is_fallback": bool(row["is_fallback"]),
        })

    return result


# ─── Test ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()

    dummy_results = [
        {"response_time": 2.1, "input_tokens": 1200, "output_tokens": 150,
         "tokens": 1350, "is_fallback": False},
        {"response_time": 1.8, "input_tokens": 980,  "output_tokens": 200,
         "tokens": 1180, "is_fallback": False},
        {"response_time": 0.9, "input_tokens": 500,  "output_tokens": 50,
         "tokens": 550,  "is_fallback": True},
    ]
    dummy_sources = [
        ["Case #04 — Fighter Overheat (Fighter X)", "Troubleshooting Fighter X → 2. Engine Overheating"],
        ["SOP Fighter X → 4. Filter Replacement"],
        [],
    ]
    dummy_queries = [
        "Fighter overheat di tanjakan",
        "Interval filter udara Fighter X",
        "Pertanyaan yang tidak ada jawabannya",
    ]

    for q, r, s in zip(dummy_queries, dummy_results, dummy_sources):
        log_query(q, r, s)

    stats = get_stats()
    print("=== STATS ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\n=== RECENT LOGS ===")
    for row in get_recent_logs():
        print(f"  [{row['timestamp']}] {row['query']} | {row['response_time']}s | fallback={row['is_fallback']}")
