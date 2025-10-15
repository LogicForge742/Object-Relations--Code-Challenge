
#  MAGAZINE MODEL (lib/magazine.py)

# Represents a magazine that contains multiple articles.
# Handles:
# - Validated read/write properties (name, category)
# - Database CRUD operations (INSERT / UPDATE)
# - Relationships to articles and authors
# - Utility and aggregate methods
#
# Uses direct SQLite access (via `get_connection`) — no ORM.


import sys
from .database_utils import get_connection


class Magazine:
    def __init__(self, id=None, name=None, category=None):
        """
        Initialize a new Magazine instance.

        Args:
            id (int, optional): The magazine's database ID (primary key)
            name (str): The magazine's title/name
            category (str): The magazine's content category
        """
        self.id = id
        self._name = None
        self._category = None

        # Validate and set name/category via their setters
        self.name = name
        self.category = category

   
    #  PROPERTIES (Validation Logic)
    

    # --- name property ---
    @property
    def name(self):
        """Return the magazine's name (read access)."""
        return self._name

    @name.setter
    def name(self, value):
        """Set and validate the magazine's name."""
        if not isinstance(value, str):
            raise TypeError("Magazine name must be a string.")
        if len(value.strip()) == 0:
            raise ValueError("Magazine name cannot be empty.")
        self._name = value.strip()  # Store clean, trimmed value

    # --- category property ---
    @property
    def category(self):
        """Return the magazine's category (read access)."""
        return self._category

    @category.setter
    def category(self, value):
        """Set and validate the magazine's category."""
        if not isinstance(value, str):
            raise TypeError("Magazine category must be a string.")
        if len(value.strip()) == 0:
            raise ValueError("Magazine category cannot be empty.")
        self._category = value.strip()

   
    #  CLASS METHODS (Helpers for DB interaction)
   
    @classmethod
    def new_from_db(cls, row):
        """
        Create a Magazine instance from a database row.

        Args:
            row (sqlite3.Row): Row fetched from the DB.
        Returns:
            Magazine: A fully populated Magazine instance.
        """
        return cls(id=row["id"], name=row["title"], category=row["category"])

    @classmethod
    def find_by_id(cls, id):
        """
        Retrieve a Magazine record by its unique ID.

        Args:
            id (int): Primary key of the magazine.
        Returns:
            Magazine | None
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM magazines WHERE id = ?", (id,))
        row = cursor.fetchone()

        # ⚠️ Keep shared DB open during pytest, but close in production.
        if "pytest" not in sys.modules:
            conn.close()

        return cls.new_from_db(row) if row else None

    #  SAVE (INSERT / UPDATE)
    def save(self):
        """
        Insert a new record or update an existing one in the `magazines` table.
        Automatically handles whether the instance is new or existing.
        """
        conn = get_connection()
        cursor = conn.cursor()

        if self.id is None:
            # 🔹 Insert a new magazine record
            cursor.execute(
                "INSERT INTO magazines (title, category) VALUES (?, ?)",
                (self.name, self.category)
            )
            self.id = cursor.lastrowid  # Fetch the new auto-generated ID
        else:
            # 🔹 Update an existing magazine record
            cursor.execute(
                "UPDATE magazines SET title = ?, category = ? WHERE id = ?",
                (self.name, self.category, self.id)
            )

        conn.commit()

        # Only close DB in production (not in pytest mode)
        if "pytest" not in sys.modules:
            conn.close()

    #  RELATIONSHIP METHODS
  
    def articles(self):
        """
        Retrieve all Article instances that belong to this magazine.

        Returns:
            list[Article]
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE magazine_id = ?", (self.id,))
        rows = cursor.fetchall()

        # Import here to avoid circular dependency between files
        from .article import Article
        return [Article.new_from_db(row) for row in rows]

    def contributors(self):
        """
        Retrieve all unique Authors who have written for this magazine.

        Returns:
            list[Author]
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT a.*
            FROM authors a
            JOIN articles ar ON ar.author_id = a.id
            WHERE ar.magazine_id = ?
        """, (self.id,))
        rows = cursor.fetchall()

        from .author import Author
        return [Author.new_from_db(row) for row in rows]

    #  EXTRA METHODS (Convenience / Aggregations)
   
    def article_titles(self):
        """
        Return a list of all article titles published in this magazine.

        Returns:
            list[str]
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM articles WHERE magazine_id = ?", (self.id,))
        rows = cursor.fetchall()
        return [row["title"] for row in rows]

    def contributing_authors(self):
        """
        Return a list of Authors who have written more than 2 articles
        for this magazine.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT author_id
            FROM articles
            WHERE magazine_id = ?
            GROUP BY author_id
            HAVING COUNT(id) > 2
        """, (self.id,))
        author_rows = cursor.fetchall()
        author_ids = [row["author_id"] for row in author_rows]

        from .author import Author
        return [Author.find_by_id(aid) for aid in author_ids]

    #  BONUS: TOP PUBLISHER (Aggregate Method)
   
    @classmethod
    def top_publisher(cls):
        """
        Find the magazine with the highest number of articles.

        Returns:
            Magazine | None: The top publisher, or None if no articles exist.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT magazine_id, COUNT(id) AS total_articles
            FROM articles
            GROUP BY magazine_id
            ORDER BY total_articles DESC
            LIMIT 1
        """)
        row = cursor.fetchone()

        # If there are no articles, return None
        if not row:
            return None

        # Otherwise, return the magazine instance with that ID
        return cls.find_by_id(row["magazine_id"])
