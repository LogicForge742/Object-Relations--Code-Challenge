# main.py
from database_utils import get_connection

def main():
    print(" Starting OBJECT-RELATIONS app...")

    #  Get a connection to the database
    conn = get_connection()
    cursor = conn.cursor()

    #  Insert sample data (optional)
    print("\n Seeding database with sample data...")
    cursor.execute("INSERT OR IGNORE INTO authors (name, email) VALUES (?, ?);", ("Milton Ngeno", "milton@example.com"))
    cursor.execute("INSERT OR IGNORE INTO magazines (title, category) VALUES (?, ?);", ("Tech Weekly", "Technology"))

    # Get author and magazine IDs
    cursor.execute("SELECT id FROM authors WHERE name = ?", ("Milton Ngeno",))
    author_id = cursor.fetchone()["id"]
    cursor.execute("SELECT id FROM magazines WHERE title = ?", ("Tech Weekly",))
    magazine_id = cursor.fetchone()["id"]

    # Add article linked to author and magazine
    cursor.execute("""
        INSERT OR IGNORE INTO articles (title, content, author_id, magazine_id)
        VALUES (?, ?, ?, ?);
    """, ("The Future of AI", "AI will shape the next generation of tech.", author_id, magazine_id))

    conn.commit()
    print("Sample data inserted!")

    #Fetch and display data
    print("\nCurrent Data in Database:")
    print("\nAuthors:")
    for row in cursor.execute("SELECT * FROM authors;"):
        print(f"- {row['name']} ({row['email']})")

    print("\nMagazines:")
    for row in cursor.execute("SELECT * FROM magazines;"):
        print(f"- {row['title']} [{row['category']}]")

    print("\nArticles:")
    for row in cursor.execute("""
        SELECT a.title, a.content, au.name AS author_name, m.title AS magazine_title
        FROM articles a
        JOIN authors au ON a.author_id = au.id
        JOIN magazines m ON a.magazine_id = m.id;
    """):
        print(f"- '{row['title']}' by {row['author_name']} in {row['magazine_title']}")

    # Close connection
    conn.close()
    print("\n Done. Database connection closed.")

if __name__ == "__main__":
    main()
