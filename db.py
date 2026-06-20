import os
import sqlite3


SQLITE_DB_PATH = "hebrew_vocab.db"


class CursorAdapter:
    def __init__(self, cursor, database_type):
        self.cursor = cursor
        self.database_type = database_type

    def execute(self, query, params=None):
        if self.database_type == "sqlite":
            query = query.replace("%s", "?")

        if params is None:
            return self.cursor.execute(query)

        return self.cursor.execute(query, params)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()


class ConnectionAdapter:
    def __init__(self, connection, database_type):
        self.connection = connection
        self.database_type = database_type

    def cursor(self):
        return CursorAdapter(
            self.connection.cursor(),
            self.database_type
        )

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


def get_database_type():
    if os.getenv("DATABASE_URL"):
        return "postgresql"

    return "sqlite"


def get_connection():
    database_type = get_database_type()

    if database_type == "postgresql":
        from psycopg import connect
        from psycopg.rows import dict_row

        conn = connect(
            os.environ["DATABASE_URL"],
            row_factory=dict_row
        )

        return ConnectionAdapter(conn, "postgresql")

    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row

    return ConnectionAdapter(conn, "sqlite")


def column_exists(cur, table_name, column_name, database_type):
    if database_type == "postgresql":
        cur.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = %s
              AND column_name = %s
            """,
            (table_name, column_name)
        )
    else:
        cur.execute(f"PRAGMA table_info({table_name})")
        return any(column["name"] == column_name for column in cur.fetchall())

    return cur.fetchone() is not None


def ensure_column(cur, table_name, column_name, definition, database_type):
    if not column_exists(cur, table_name, column_name, database_type):
        cur.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    database_type = get_database_type()

    if database_type == "postgresql":
        cur.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id BIGSERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id BIGSERIAL PRIMARY KEY,
            hebrew TEXT NOT NULL,
            hebrew_pointed TEXT,
            hebrew_no_niqqud TEXT,
            transliteration TEXT,
            part_of_speech TEXT,
            english_meaning TEXT NOT NULL,
            japanese_meaning TEXT,
            example_hebrew TEXT,
            example_english TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (hebrew, english_meaning)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS folder_words (
            id BIGSERIAL PRIMARY KEY,
            folder_id BIGINT NOT NULL,
            word_id BIGINT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            priority INTEGER DEFAULT 0,
            FOREIGN KEY (folder_id) REFERENCES folders(id),
            FOREIGN KEY (word_id) REFERENCES words(id),
            UNIQUE(folder_id, word_id)
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id BIGSERIAL PRIMARY KEY,
            word_id BIGINT NOT NULL,
            folder_id BIGINT,
            mode TEXT NOT NULL,
            result TEXT NOT NULL,
            reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (word_id) REFERENCES words(id),
            FOREIGN KEY (folder_id) REFERENCES folders(id)
        )
        """)

        ensure_column(cur, "words", "japanese_meaning", "TEXT", database_type)
        ensure_column(
            cur,
            "words",
            "updated_at",
            "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            database_type
        )

    else:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
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
            japanese_meaning TEXT,
            example_hebrew TEXT,
            example_english TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (hebrew, english_meaning)
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

        ensure_column(cur, "words", "japanese_meaning", "TEXT", database_type)
        ensure_column(
            cur,
            "words",
            "updated_at",
            "TEXT DEFAULT CURRENT_TIMESTAMP",
            database_type
        )

    conn.commit()
    conn.close()
