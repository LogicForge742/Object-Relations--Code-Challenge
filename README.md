#  Magazine Object-Relations Code Challenge

This project implements a lightweight **Object-Relational Mapping (ORM)-like system** in Python — built **without using any external ORM library** such as SQLAlchemy.  
It models relationships between **Authors**, **Magazines**, and **Articles** using **pure SQL** and **object-oriented programming principles**.

---

##  Features

 **Three Core Models**
- `Author`, `Magazine`, and `Article` — each with strict data validation.  
- Implements one-to-many and many-to-many relationships using SQL joins.

 **SQLite Database**
- Lightweight local database.  
- Tables are automatically created when the app runs.

 **Relationships**
- Easily fetch related data, e.g.:
  - `author.articles()` → all articles by an author  
  - `magazine.contributors()` → all authors who wrote for a magazine  
  - `author.magazines()` → all magazines an author has written for  

 **Testing**
- Fully tested with `pytest` for reliability and correctness.  

**No ORM**
- Pure SQL queries for educational transparency and hands-on learning.

---

##  Project Structure

Object-Relations/
│
├── lib/
│ ├── author.py # Author model
│ ├── magazine.py # Magazine model
│ ├── article.py # Article model
│ ├── database_utils.py # SQLite connection and setup
│ └── tests/ # Pytest test files
│
├── requirements.txt
├── README.md
└── .gitignore


---

##  Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Object-Relations.git
cd Object-Relations

2. Create and Activate a Virtual Environment:

python -m venv venv
source venv/bin/activate     # macOS / Linux
# OR
venv\Scripts\activate        # Windows


3. Install Dependencies:
 
 pip install -r requirements.txt

Running Tests

Run all tests to ensure your setup is correct:
pytest


Running Tests

Run all tests to ensure your setup is correct:
