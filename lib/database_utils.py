import sqlite3
import sys

# Global shared connection (used for pytest)
_shared_connection = None

DB_FILE = "magazine.db"


def get_connection():
    """
    Returns a SQLite connection object.

    🔹 In normal mode:
        - Connects to a persistent on-disk database 'magazine.db'.
    🔹 In test mode (when running under pytest):
        - Creates a single shared in-memory database that stays alive
          for all test connections.
    """

    global _shared_connection

    # 🧪 TEST MODE: detect if pytest is running
    if "pytest" in sys.modules:
        if _shared_connection is None:
            # Create one shared in-memory database
            _shared_connection = sqlite3.connect(
                "file:shared_memdb?mode=memory&cache=shared",
                uri=True,
                check_same_thread=False,
            )
            _shared_connection.row_factory = sqlite3.Row
            print("🧪 Created shared in-memory database for testing...")

            # ✅ Create tables right after connection
            create_tables(_shared_connection)

        else:
            # Ensure connection still open
            try:
                _shared_connection.execute("SELECT 1;")
            except sqlite3.ProgrammingError:
                print("⚠️ Reopening closed shared test database connection...")
                _shared_connection = sqlite3.connect(
                    "file:shared_memdb?mode=memory&cache=shared",
                    uri=True,
                    check_same_thread=False,
                )
                _shared_connection.row_factory = sqlite3.Row
                create_tables(_shared_connection)

        return _shared_connection

    #  NORMAL MODE (persistent DB file)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    print(f"Connected to persistent database: {DB_FILE}")
    create_tables(conn)
    return conn


def create_tables(conn):
    """
    Ensures all required tables exist.
    This runs every time a new connection is made.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    #  Authors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        );
    """)

    #  Magazines table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS magazines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL
        );
    """)

    #  Articles table (with FKs)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            author_id INTEGER NOT NULL,
            magazine_id INTEGER NOT NULL,
            FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE,
            FOREIGN KEY (magazine_id) REFERENCES magazines(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    print("Tables ensured in database.")
