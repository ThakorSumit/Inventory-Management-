"""Entry point: run this file to start the app."""
import os
import sys

# Ensure current script directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


import database as db
from gui import InventoryApp

if __name__ == "__main__":
    db.init_db()
    app = InventoryApp()
    app.mainloop()
