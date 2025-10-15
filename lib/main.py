from database_utils import get_connection

def add_author(conn):
    name = input("Enter author name: ")
    email = input("Enter author email: ")

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO authors (name, email) VALUES (?, ?)", (name, email))
        conn.commit()
        print(" Author added successfully!")
    except Exception as e:
        print(f" Error adding author: {e}")

def add_magazine(conn):
    title = input("Enter magazine title: ")
    category = input("Enter magazine category: ")

    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO magazines (title, category) VALUES (?, ?)", (title, category))
        conn.commit()
        print(" Magazine added successfully!")
    except Exception as e:
        print(f" Error adding magazine: {e}")

def add_article(conn):
    title = input("Enter article title: ")
    content = input("Enter article content: ")
    author_id = input("Enter author ID: ")
    magazine_id = input("Enter magazine ID: ")

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO articles (title, content, author_id, magazine_id)
            VALUES (?, ?, ?, ?)
        """, (title, content, author_id, magazine_id))
        conn.commit()
        print(" Article added successfully!")
    except Exception as e:
        print(f"Error adding article: {e}")

def view_articles(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.title, au.name AS author, m.title AS magazine
        FROM articles a
        JOIN authors au ON a.author_id = au.id
        JOIN magazines m ON a.magazine_id = m.id;
    """)

    articles = cursor.fetchall()
    if not articles:
        print(" No articles found.")
        return

    print("\n Articles List:")
    print("-" * 60)
    for row in articles:
        print(f"ID: {row['id']}, Title: {row['title']}, Author: {row['author']}, Magazine: {row['magazine']}")
    print("-" * 60)

def main():
    conn = get_connection()

    while True:
        print("\n=========  MAGAZINE MANAGEMENT MENU =========")
        print("1️⃣  Add Author")
        print("2️⃣  Add Magazine")
        print("3️⃣  Add Article")
        print("4️⃣  View Articles")
        print("5️⃣  Exit")
        print("===============================================")

        choice = input("Enter your choice (1-5): ")

        if choice == "1":
            add_author(conn)
        elif choice == "2":
            add_magazine(conn)
        elif choice == "3":
            add_article(conn)
        elif choice == "4":
            view_articles(conn)
        elif choice == "5":
            print("Goodbye!")
            break
        else:
            print(" Invalid choice. Please enter a number from 1 to 5.")

    conn.close()

if __name__ == "__main__":
    main()
