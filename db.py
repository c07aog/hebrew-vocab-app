import sqlite3

DB_PATH = "hebrew_vocab.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS folders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hebrew TEXT NOT NULL,
        hebrew_pointed TEXT,
        hebrew_no_niqqud TEXT,
        transliteration TEXT,
        part_of_speech TEXT,
        english_meaning TEXT NOT NULL,
        example_hebrew TEXT,
        example_english TEXT,
        notes TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS folder_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        folder_id INTEGER NOT NULL,
        word_id INTEGER NOT NULL,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP,
        priority INTEGER DEFAULT 0,
        FOREIGN KEY (folder_id) REFERENCES folders(id),
        FOREIGN KEY (word_id) REFERENCES words(id),
        UNIQUE(folder_id, word_id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word_id INTEGER NOT NULL,
        folder_id INTEGER,
        mode TEXT NOT NULL,
        result TEXT NOT NULL,
        reviewed_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (word_id) REFERENCES words(id),
        FOREIGN KEY (folder_id) REFERENCES folders(id)
    )
    """)

    conn.commit()
    conn.close()