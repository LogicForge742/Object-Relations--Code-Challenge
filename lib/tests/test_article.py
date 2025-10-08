import pytest
from pytest_mock import MockerFixture

from lib.author import Author
from lib.database_utils import get_connection

# ---------------------------------------------------
# Setup: create and reset tables before each test
# ---------------------------------------------------
@pytest.fixture(autouse=True)
def setup_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS authors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS magazines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            author_id INTEGER,
            magazine_id INTEGER,
            FOREIGN KEY (author_id) REFERENCES authors(id),
            FOREIGN KEY (magazine_id) REFERENCES magazines(id)
        )
    """)

    cur.execute("DELETE FROM articles")
    cur.execute("DELETE FROM magazines")
    cur.execute("DELETE FROM authors")

    conn.commit()
    if "pytest" not in __import__("sys").modules:
        conn.close()

# ---------------------------------------------------
# Test: Saving a new author inserts and find_by_id retrieves it
# ---------------------------------------------------
def test_save_inserts_and_find_by_id_retrieves():
    author = Author(name="Alice", email="alice@example.com")
    author.save()

    assert author.id is not None and isinstance(author.id, int)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM authors WHERE id = ?", (author.id,))
    row = cur.fetchone()
    assert row is not None
    assert row["name"] == "Alice"
    assert row["email"] == "alice@example.com"

    fetched = Author.find_by_id(author.id)
    assert isinstance(fetched, Author)
    assert fetched.id == author.id
    assert fetched.name == "Alice"
    assert fetched.email == "alice@example.com"

# ---------------------------------------------------
# Test: Updating existing author modifies fields without changing id
# ---------------------------------------------------
def test_save_updates_existing_author_without_changing_id():
    original = Author(name="Bob", email="old@example.com")
    original.save()
    original_id = original.id

    updated = Author(id=original_id, name="Robert", email="new@example.com")
    updated.save()

    assert updated.id == original_id

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS cnt FROM authors")
    count_row = cur.fetchone()
    assert count_row["cnt"] == 1

    cur.execute("SELECT * FROM authors WHERE id = ?", (original_id,))
    row = cur.fetchone()
    assert row["name"] == "Robert"
    assert row["email"] == "new@example.com"

# ---------------------------------------------------
# Test: add_article persists and links to author and magazine, and articles() reflects it
# ---------------------------------------------------
def test_add_article_persists_and_links_to_author_and_magazine(mocker: MockerFixture):
    # Prepare author
    author = Author(name="Writer", email="writer@example.com")
    author.save()

    # Insert a magazine row and create a mocked Magazine class/instance
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO magazines (title, category) VALUES (?, ?)",
        ("Tech Daily", "Technology")
    )
    mag_id = cur.lastrowid
    conn.commit()

    class FakeMagazine:
        def __init__(self, id=None):
            self.id = id

    mocker.patch("lib.magazine.Magazine", new=FakeMagazine)
    magazine = FakeMagazine(id=mag_id)

    # Mock Article to control persistence and loading
    class FakeArticle:
        def __init__(self, title, content, author, magazine):
            self.id = None
            self.title = title
            self.content = content
            self.author = author
            self.magazine = magazine

        def save(self):
            c = get_connection().cursor()
            c.execute(
                "INSERT INTO articles (title, content, author_id, magazine_id) VALUES (?, ?, ?, ?)",
                (self.title, self.content, self.author.id, self.magazine.id),
            )
            self.id = c.lastrowid
            get_connection().commit()

        @classmethod
        def new_from_db(cls, row):
            obj = cls(title=row["title"], content=row["content"], author=object(), magazine=object())
            obj.id = row["id"]
            return obj

    mocker.patch("lib.article.Article", new=FakeArticle)

    # Act
    created_article = author.add_article(magazine, title="Hello World")

    # Assert article created and saved
    assert isinstance(created_article, FakeArticle)
    assert created_article.id is not None

    # articles() should reflect the link
    authored_articles = author.articles()
    assert len(authored_articles) == 1
    assert isinstance(authored_articles[0], FakeArticle)
    assert authored_articles[0].title == "Hello World"
    assert authored_articles[0].id == created_article.id

# ---------------------------------------------------
# Test: Invalid initialization names raise ValueError
# ---------------------------------------------------
def test_init_raises_value_error_for_invalid_name():
    with pytest.raises(ValueError):
        Author(name=123, email="x@example.com")
    with pytest.raises(ValueError):
        Author(name="   ", email="x@example.com")

# ---------------------------------------------------
# Test: name is read-only after initialization
# ---------------------------------------------------
def test_name_property_is_read_only():
    author = Author(name="Immutable", email="i@example.com")
    with pytest.raises(AttributeError):
        author.name = "Changed"

# ---------------------------------------------------
# Test: add_article raises TypeError for non-Magazine parameter
# ---------------------------------------------------
def test_add_article_raises_type_error_for_non_magazine():
    author = Author(name="TypeSafe", email="t@example.com")
    author.save()
    with pytest.raises(TypeError):
        author.add_article(magazine="not-a-magazine", title="Oops")