
#  AUTHOR MODEL

# Represents an author who writes articles for magazines.
# Implements:
# - Read-only validated `name` property
# - Database persistence (INSERT / UPDATE)
# - Relationship methods to retrieve related records
# Uses direct SQL (no ORM).


from .database_utils import get_connection


class Author:
    def __init__(self, id=None, name=None, email=None):
        """
        Initialize an Author instance.
        Args:
            id (int, optional): Auto-generated primary key from DB.
            name (str, optional): Author's name.
            email (str, optional): Author's email.
        """
        self.id = id
        self._name = None
        self.email = email

        # Only validate if a name was provided (useful when loading from DB)
        if name is not None:
            if not isinstance(name, str):
                raise ValueError("Author name must be a string.")
            if not name.strip():
                raise ValueError("Author name cannot be empty.")
            self._name = name

   
    #  PROPERTIES
 
    @property
    def name(self):
        """Read-only property for the author's validated name."""
        return self._name

   
    # CLASS METHODS (DB HELPERS)
   
    @classmethod
    def new_from_db(cls, row):
        """
        Build an Author instance from a database row (sqlite3.Row).
        """
        return cls(id=row["id"], name=row["name"], email=row["email"])

    @classmethod
    def find_by_id(cls, id):
        """
        Find an Author by ID.
        Returns:
            Author | None
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM authors WHERE id = ?", (id,))
        row = cursor.fetchone()

        #  Do NOT close the shared connection (used in tests)
        return cls.new_from_db(row) if row else None


    #  SAVE METHOD (INSERT / UPDATE)
  
    def save(self):
        """
        Save the Author record in the database.
        - INSERT if no ID.
        - UPDATE if ID exists.
        """
        conn = get_connection()
        cursor = conn.cursor()

        if self.id is None:
            # 🔹 Insert new author
            cursor.execute(
                "INSERT INTO authors (name, email) VALUES (?, ?)",
                (self.name, self.email),
            )
            self.id = cursor.lastrowid
        else:
            # 🔹 Update existing author
            cursor.execute(
                "UPDATE authors SET name = ?, email = ? WHERE id = ?",
                (self.name, self.email, self.id),
            )

        conn.commit()
        # Do NOT close — keep the shared in-memory DB alive.

    
    #  RELATIONSHIP METHODS
  
    def articles(self):
        """
        Return all articles written by this author.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE author_id = ?", (self.id,))
        rows = cursor.fetchall()

        # Import here to avoid circular dependency
        from .article import Article
        return [Article.new_from_db(row) for row in rows]

    def magazines(self):
        """
        Return all unique magazines this author has written for.
        """
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT m.*
            FROM magazines m
            JOIN articles a ON a.magazine_id = m.id
            WHERE a.author_id = ?
            """,
            (self.id,),
        )
        rows = cursor.fetchall()

        from .magazine import Magazine
        return [Magazine.new_from_db(row) for row in rows]

    #  EXTRA METHODS
  
    def add_article(self, magazine, title):
        """
        Create and save a new Article written by this author for a given magazine.
        """
        from .article import Article
        from .magazine import Magazine

        if not isinstance(magazine, Magazine):
            raise TypeError("magazine must be a Magazine instance.")

        # Create and persist new Article
        article = Article(title=title, content="", author=self, magazine=magazine)
        article.save()
        return article

    def topic_areas(self):
        """
        Return a list of unique categories from magazines this author has written in.
        Example: ['Technology', 'Health']
        """
        mags = self.magazines()
        return list({mag.category for mag in mags})
