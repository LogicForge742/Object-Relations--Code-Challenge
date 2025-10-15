from .database_utils import get_connection

class Article:
    def __init__(self, id=None, title=None, content=None, author=None, magazine=None):
        """
        Initialize an Article instance.

        Args:
            id (int): Unique identifier (optional, set by DB)
            title (str): Title of the article (validated, read-only)
            content (str): Body/content of the article
            author (Author): The Author object who wrote this article
            magazine (Magazine): The Magazine object where it was published
        """
        self.id = id
        self._title = None     # Private attribute (read-only property)
        self.title = title     # Calls validation
        self.content = content
        self.author = author           # Must be an Author object
        self.magazine = magazine       # Must be a Magazine object

    
    #  PROPERTY: title (READ-ONLY)

    @property
    def title(self):
        """Return the article's title."""
        return self._title

    @title.setter
    def title(self, value):
        """
        Validate title:
          - Must be a string
          - Cannot be empty or only spaces
        """
        if not isinstance(value, str):
            raise TypeError("Article title must be a string.")
        if len(value.strip()) == 0:
            raise ValueError("Article title cannot be empty.")
        self._title = value.strip()

    
    #  RELATIONSHIP PROPERTIES (author, magazine)
    

    @property
    def author(self):
        """Return the Author object for this article."""
        return self._author

    @author.setter
    def author(self, value):
        """
        Ensure the author is an instance of Author or None.
        This enforces the relationship integrity.
        """
        if value is not None:
            from .author import Author
            if not isinstance(value, Author):
                raise TypeError("author must be an Author instance.")
        self._author = value

    @property
    def magazine(self):
        """Return the Magazine object for this article."""
        return self._magazine

    @magazine.setter
    def magazine(self, value):
        """
        Ensure the magazine is an instance of Magazine or None.
        """
        if value is not None:
            from .magazine import Magazine
            if not isinstance(value, Magazine):
                raise TypeError("magazine must be a Magazine instance.")
        self._magazine = value

    #  CLASS METHODS — Create or find records
   

    @classmethod
    def new_from_db(cls, row):
        """
        Create an Article instance from a DB row.
        Links the Author and Magazine via their IDs.
        """
        from .author import Author
        from .magazine import Magazine

        author = Author.find_by_id(row["author_id"])
        magazine = Magazine.find_by_id(row["magazine_id"])

        return cls(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            author=author,
            magazine=magazine
        )

    @classmethod
    def find_by_id(cls, id):
        """Find an article by its ID."""
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articles WHERE id = ?", (id,))
        row = cursor.fetchone()
        conn.close()

        return cls.new_from_db(row) if row else None

   
    #  SAVE (INSERT / UPDATE)
 

    def save(self):
        """
        Save or update the article record.
        Uses author.id and magazine.id as foreign keys.
        """
        if not self.author or not self.magazine:
            raise ValueError("Article must have an author and a magazine before saving.")

        conn = get_connection()
        cursor = conn.cursor()

        if self.id is None:
            # INSERT new record
            cursor.execute(
                """
                INSERT INTO articles (title, content, author_id, magazine_id)
                VALUES (?, ?, ?, ?)
                """,
                (self.title, self.content, self.author.id, self.magazine.id)
            )
            self.id = cursor.lastrowid
        else:
            # UPDATE existing record
            cursor.execute(
                """
                UPDATE articles
                SET title = ?, content = ?, author_id = ?, magazine_id = ?
                WHERE id = ?
                """,
                (self.title, self.content, self.author.id, self.magazine.id, self.id)
            )

        conn.commit()
        conn.close()
    if __name__ == "__main__":
        print("article.py is running successfully!")
