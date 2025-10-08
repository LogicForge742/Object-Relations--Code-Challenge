import pytest
from lib.magazine import Magazine
from lib.database_utils import get_connection

# ---------------------------------------------------
# 🧪 Setup: Creates and resets all relevant tables before each test
# ---------------------------------------------------
@pytest.fixture(autouse=True)
def setup_db():
    conn = get_connection()
    cur = conn.cursor()

    # Create tables if not exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS magazines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author_id INTEGER,
            magazine_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES authors(id),
            FOREIGN KEY (magazine_id) REFERENCES magazines(id)
        )
    """)

    # Clean all existing records
    cur.execute("DELETE FROM articles")
    cur.execute("DELETE FROM magazines")
    cur.execute("DELETE FROM authors")

    conn.commit()
    # ❗ Do NOT close connection in pytest mode
    # Closing an in-memory shared DB wipes all data
    if "pytest" not in __import__("sys").modules:
        conn.close()

# ---------------------------------------------------
# 🧩 Test: Saving a new magazine inserts and assigns an ID
# ---------------------------------------------------
def test_save_inserts_new_magazine_and_sets_id():
    mag = Magazine(name="Tech Weekly", category="Technology")
    mag.save()

    assert mag.id is not None and isinstance(mag.id, int)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM magazines WHERE id = ?", (mag.id,))
    row = cur.fetchone()

    assert row is not None
    assert row["title"] == "Tech Weekly"
    assert row["category"] == "Technology"

# ---------------------------------------------------
# 🔁 Test: Updating an existing magazine modifies its record, not inserts new one
# ---------------------------------------------------
def test_save_updates_existing_magazine_by_id():
    mag = Magazine(name="Initial Title", category="Initial Category")
    mag.save()
    original_id = mag.id

    mag.name = "Updated Title"
    mag.category = "Updated Category"
    mag.save()

    assert mag.id == original_id

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM magazines")
    count_row = cur.fetchone()
    cur.execute("SELECT * FROM magazines WHERE id = ?", (original_id,))
    row = cur.fetchone()

    assert count_row["cnt"] == 1
    assert row["title"] == "Updated Title"
    assert row["category"] == "Updated Category"

# ---------------------------------------------------
# 🔎 Test: Finding a magazine by ID returns a Magazine instance
# ---------------------------------------------------
def test_find_by_id_returns_magazine_instance():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO magazines (title, category) VALUES (?, ?)",
        ("World News", "News")
    )
    inserted_id = cur.lastrowid
    conn.commit()

    mag = Magazine.find_by_id(inserted_id)
    assert isinstance(mag, Magazine)
    assert mag.id == inserted_id
    assert mag.name == "World News"
    assert mag.category == "News"

# ---------------------------------------------------
# ⚠️ Test: Reject invalid or empty magazine name
# ---------------------------------------------------
def test_name_setter_rejects_empty_or_whitespace():
    mag = Magazine(name="Valid Name", category="Valid Category")
    with pytest.raises(ValueError):
        mag.name = ""
    with pytest.raises(ValueError):
        mag.name = "   "

# ---------------------------------------------------
# ⚠️ Test: Reject invalid name or category types
# ---------------------------------------------------
def test_init_rejects_non_string_name_or_category():
    with pytest.raises(TypeError):
        Magazine(name=None, category="Category")
    with pytest.raises(TypeError):
        Magazine(name="Name", category=None)

# ---------------------------------------------------
# 🧮 Test: Top publisher should return None if there are no articles
# ---------------------------------------------------
def test_top_publisher_returns_none_when_no_articles():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM articles")
    conn.commit()

    assert Magazine.top_publisher() is None
