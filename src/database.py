import os
import sqlite3

# Define the database path
DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data")) 
DB_PATH = os.path.join(DB_DIR, "gallery.db")


def init_db():
    # make sure the data directory exists  
    os.makedirs(DB_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor() 

    # create the games table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL UNIQUE,
            release_date TEXT,
            cover_url TEXT,
            local_cover_path TEXT,
            developer TEXT,
            genre TEXT,
            description TEXT,
            status TEXT DEFAULT 'Backlog'
        )
    """
    )

    conn.commit()
    conn.close()


def add_game( # all parameters for the game
    title,
    release_date,
    cover_url,
    local_cover_path,
    developer,
    genre,
    description,
    status="Backlog",
):
    # inserts a new game into the database. returns true if successful, false if title exists
    conn = sqlite3.connect(DB_PATH) 
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO games (title, release_date, cover_url, local_cover_path, developer, genre, description, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                title,
                release_date,
                cover_url,
                local_cover_path,
                developer,
                genre,
                description,
                status,
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # title uniqueness constraint failed
        return False
    finally:
        conn.close()


def get_all_games():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows us to access columns by name like row['title']
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM games ORDER BY title ASC")
    rows = cursor.fetchall()

    # Convert list of sqlite3.Row to list of dicts
    games = [dict(row) for row in rows]
    conn.close()
    return games

def update_game(game_id, title, release_date, developer, genre, description, status):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE games 
            SET title = ?, release_date = ?, developer = ?, genre = ?, description = ?, status = ?
            WHERE id = ?
        """,
            (
                title,
                release_date,
                developer,
                genre,
                description,
                status,
                game_id,
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Title unique constraint failed (if they try to rename it to a title that already exists)
        return False
    finally:
        conn.close()


def delete_game(game_id):
    #delete a game from db by id
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM games WHERE id = ?", (game_id,))
    conn.commit()
    conn.close()