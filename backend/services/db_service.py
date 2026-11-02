import sqlite3
import datetime
import os
import config

def get_connection():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        sign_detected TEXT NOT NULL,
        confidence REAL NOT NULL,
        target_lang TEXT NOT NULL,
        translation TEXT NOT NULL,
        source TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS training_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        samples_count INTEGER,
        classes_count INTEGER,
        accuracy REAL,
        f1_score REAL,
        status TEXT NOT NULL,
        message TEXT
    );
    """)

    conn.commit()
    conn.close()

def add_history_entry(sign_detected: str, confidence: float, target_lang: str, translation: str, source: str) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO history (timestamp, sign_detected, confidence, target_lang, translation, source)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (now_iso, sign_detected, float(confidence), target_lang, translation, source))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": new_id,
        "timestamp": now_iso,
        "sign_detected": sign_detected,
        "confidence": confidence,
        "target_lang": target_lang,
        "translation": translation,
        "source": source
    }

def get_history(limit: int = 50, offset: int = 0, source: str = None) -> list[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    
    if source:
        cursor.execute("""
            SELECT id, timestamp, sign_detected, confidence, target_lang, translation, source
            FROM history
            WHERE source = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (source, limit, offset))
    else:
        cursor.execute("""
            SELECT id, timestamp, sign_detected, confidence, target_lang, translation, source
            FROM history
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def clear_history():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history")
    conn.commit()
    conn.close()

def delete_history_entry(entry_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM history WHERE id = ?", (entry_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_system_stats() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM history")
    total_detections = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT sign_detected) FROM history")
    unique_signs = cursor.fetchone()[0]
    
    cursor.execute("SELECT timestamp FROM history ORDER BY id DESC LIMIT 1")
    last_row = cursor.fetchone()
    last_detection = last_row[0] if last_row else None
    
    conn.close()
    return {
        "total_detections": total_detections,
        "unique_signs": unique_signs,
        "last_detection": last_detection
    }
