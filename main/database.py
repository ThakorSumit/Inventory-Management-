"""Database layer: all SQLite code lives here."""
import csv
import sqlite3

DB_NAME = "inventory.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    with connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                quantity INTEGER NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0
            )
            """
        )


def add_item(name, category, quantity, price):
    with connect() as conn:
        conn.execute(
            "INSERT INTO items (name, category, quantity, price) VALUES (?, ?, ?, ?)",
            (name, category, quantity, price),
        )


def get_items(search="", category="All", low_stock_only=False, low_stock_limit=5):
    query = "SELECT id, name, category, quantity, price FROM items WHERE (name LIKE ? OR IFNULL(category,'') LIKE ?)"
    like = f"%{search}%"
    params = [like, like]
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if low_stock_only:
        query += " AND quantity <= ?"
        params.append(low_stock_limit)
    query += " ORDER BY name COLLATE NOCASE"
    with connect() as conn:
        return conn.execute(query, params).fetchall()


def get_categories():
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category FROM items "
            "WHERE category IS NOT NULL AND category != '' ORDER BY category COLLATE NOCASE"
        ).fetchall()
    return [r[0] for r in rows]


def get_stats(low_stock_limit=5):
    with connect() as conn:
        total_products, total_units, total_value = conn.execute(
            "SELECT COUNT(*), IFNULL(SUM(quantity),0), IFNULL(SUM(quantity*price),0) FROM items"
        ).fetchone()
        low = conn.execute(
            "SELECT COUNT(*) FROM items WHERE quantity <= ?", (low_stock_limit,)
        ).fetchone()[0]
    return {
        "total_products": total_products,
        "total_units": total_units,
        "total_value": total_value,
        "low_stock_count": low,
    }


def update_item(item_id, name, category, quantity, price):
    with connect() as conn:
        conn.execute(
            "UPDATE items SET name=?, category=?, quantity=?, price=? WHERE id=?",
            (name, category, quantity, price, item_id),
        )


def adjust_quantity(item_id, delta):
    """Add/subtract stock. Quantity never goes below 0."""
    with connect() as conn:
        conn.execute(
            "UPDATE items SET quantity = MAX(0, quantity + ?) WHERE id=?",
            (delta, item_id),
        )


def delete_item(item_id):
    with connect() as conn:
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))


def export_to_csv(filepath):
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, category, quantity, price, quantity*price FROM items ORDER BY name COLLATE NOCASE"
        ).fetchall()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Name", "Category", "Quantity", "Price", "Total Value"])
        writer.writerows(rows)
