# 📦 Inventory Management

A desktop inventory manager built with Python and [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter). Track products, quantities and prices, spot low stock at a glance, and export your data to CSV.

## Features

- **Dashboard cards**: total products, total units, total stock value and low-stock alerts, updated live
- **Add / update / delete** items with name, category, quantity and unit price
- **Quick stock adjust**: +1 / -1 buttons for the selected item
- **Search** by item name or category
- **Filter** by category or show low-stock items only
- **Status colors**: ✅ In stock, ⚠️ Low stock (5 units or fewer), ❌ Out of stock
- **Sortable table**: click any column header (click again to reverse)
- **Export to CSV**
- **Light / dark mode** toggle (💡 button in the header)

## Requirements

- Python 3.8+
- customtkinter

```bash
pip install customtkinter
```

`tkinter` ships with most Python installers. On some Linux distros you may need to install it separately (e.g. `sudo apt install python3-tk`).

## Project structure

```
.
├── main.py        # main file(for run project)
├── gui.py        # CustomTkinter interface (InventoryApp)
├── database.py   # Data layer used by the GUI
└── README.md
```

## Running the app

Create the app from your entry-point script:

```python
from gui import InventoryApp

if __name__ == "__main__":
    app = InventoryApp()
    app.mainloop()
```

Then run it:

```bash
python main.py
```

## How to use

1. **Add an item**: fill in the fields on the left (name is required) and click **Add**.
2. **Edit an item**: click a row in the table, change the fields, then click **Update**.
3. **Delete an item**: select a row and click **Delete** (you'll be asked to confirm).
4. **Adjust stock quickly**: select a row and use **+1** or **-1**.
5. **Find items**: use the search box, the category dropdown, or **Low stock only**. Click **Reset** to clear all filters.
6. **Export**: click **Export CSV** and choose where to save `inventory_report.csv`.
7. **Switch theme**: click the 💡 icon in the header.

## Configuration

The low-stock threshold is set at the top of `gui.py`:

```python
LOW_STOCK_THRESHOLD = 5
```

Items with a quantity at or below this number (but above 0) are flagged as low stock.

Theme colors are defined by the constants near the top of `gui.py` (`ACCENT`, `PAGE_BG`, `CARD_BG`, `TREE_COLORS`, etc.).

## Data layer contract

`gui.py` expects `database.py` to provide these functions:

| Function | Purpose |
|---|---|
| `get_items(search, category, low_stock_only, low_stock_limit)` | Returns rows of `(id, name, category, quantity, price)` |
| `get_categories()` | Returns a list of category names |
| `get_stats(low_stock_limit)` | Returns a dict with `total_products`, `total_units`, `total_value`, `low_stock_count` |
| `add_item(name, category, quantity, price)` | Inserts a new item |
| `update_item(item_id, name, category, quantity, price)` | Updates an existing item |
| `delete_item(item_id)` | Removes an item |
| `adjust_quantity(item_id, delta)` | Adds or subtracts stock |
| `export_to_csv(path)` | Writes all items to a CSV file |


## 📸 Screenshots

- Dashboard page
 <img width="960" height="510" alt="image" src="https://github.com/user-attachments/assets/21f57f63-64ae-4f6c-a132-7a816cd7accb" />


---

## 👨‍💻 Author

**Sumit Thakor**  
[GitHub](https://github.com/ThakorSumit)
[LinkedIn](https://linkedin.com/in/sumitthakor)

---

## 📄 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
