"""GUI layer: CustomTkinter interface (rounded widgets + light/dark mode)."""
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

import database as db

LOW_STOCK_THRESHOLD = 5

ctk.set_appearance_mode("light")        # "light", "dark" or "system"
ctk.set_default_color_theme("blue")     # "blue", "green" or "dark-blue"

ACCENT = "#2563EB"
ACCENT_HOVER = "#1D4ED8"
GREEN, GREEN_HOVER = "#059669", "#047857"
RED, RED_HOVER = "#DC2626", "#B91C1C"
GRAY, GRAY_HOVER = "#64748B", "#475569"

# (light, dark) color pairs - CustomTkinter switches automatically
PAGE_BG = ("#F1F5F9", "#0F172A")
CARD_BG = ("#FFFFFF", "#1E293B")
TEXT = ("#0F172A", "#F1F5F9")
MUTED = ("#64748B", "#94A3B8")

# Treeview is a classic ttk widget, so its colors are applied manually per mode
TREE_COLORS = {
    "Light": dict(bg="#FFFFFF", fg="#0F172A", head="#F1F5F9", odd="#F8FAFC",
                  low_bg="#FEF3C7", low_fg="#B45309", out_bg="#FEE2E2", out_fg="#991B1B"),
    "Dark": dict(bg="#1E293B", fg="#E2E8F0", head="#0F172A", odd="#243247",
                 low_bg="#4A3A12", low_fg="#FBBF24", out_bg="#4C1D1D", out_fg="#FCA5A5"),
}


class InventoryApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Inventory Management")
        self.geometry("1200x780")
        self.minsize(1000, 640)
        self.configure(fg_color=PAGE_BG)

        self.selected_id = None
        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.qty_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.category_filter_var = tk.StringVar(value="All")
        self.low_stock_only_var = tk.BooleanVar(value=False)
        self.search_var.trace_add("write", lambda *a: self.refresh())

        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)   # only the table/form area stretches

        self.build_header()
        self.build_stat_cards()
        self.build_toolbar()
        self.build_main()
        self.build_status_bar()

        self.apply_tree_style()
        self.refresh_categories()
        self.refresh()

    # ---------- UI BUILDERS ----------
    def build_header(self):
        header = ctk.CTkFrame(self, corner_radius=0, fg_color=("#1E293B", "#020617"))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        ctk.CTkLabel(header, text="📦  Inventory Dashboard", text_color="#FFFFFF",
                     font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=12)

        self.mode_btn = ctk.CTkButton(header, text="💡", width=40, height=40, corner_radius=20,
                                      font=ctk.CTkFont(size=22), fg_color="transparent",
                                      hover_color="#334155", command=self.toggle_mode)
        self.mode_btn.grid(row=0, column=2, padx=16)

    def build_stat_cards(self):
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.grid(row=1, column=0, sticky="ew", padx=20, pady=(12, 4))

        self.card_vars = {k: tk.StringVar(value="0") for k in ("products", "units", "value", "low")}
        cards = [
            ("TOTAL PRODUCTS", "products", "#3B82F6"),
            ("TOTAL UNITS", "units", "#10B981"),
            ("STOCK VALUE", "value", "#8B5CF6"),
            ("LOW STOCK ALERTS", "low", "#EF4444"),
        ]
        for i, (title, key, color) in enumerate(cards):
            row.columnconfigure(i, weight=1, uniform="cards")
            card = ctk.CTkFrame(row, corner_radius=12, fg_color=CARD_BG)
            card.grid(row=0, column=i, sticky="ew", padx=(0 if i == 0 else 10, 0))

            # FIX: CTkFrame defaults to height=200, which made the cards huge.
            # height=1 lets the bar stretch to whatever height the labels need.
            ctk.CTkFrame(card, width=4, height=1, corner_radius=2, fg_color=color).pack(
                side="left", fill="y", padx=(10, 0), pady=10)

            body = ctk.CTkFrame(card, fg_color="transparent", height=1)
            body.pack(side="left", padx=12, pady=8, fill="x")
            ctk.CTkLabel(body, text=title, text_color=MUTED,
                         font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(body, textvariable=self.card_vars[key], text_color=TEXT,
                         font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")

    def build_toolbar(self):
        bar = ctk.CTkFrame(self, corner_radius=14, fg_color=CARD_BG)
        bar.grid(row=2, column=0, sticky="ew", padx=20, pady=6)

        # FIX: placeholder_text is not shown when a textvariable is attached,
        # so use an explicit label instead.
        ctk.CTkLabel(bar, text="🔍 Search", text_color=MUTED,
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(14, 6), pady=10)
        ctk.CTkEntry(bar, textvariable=self.search_var, width=260,
                     ).pack(side="left", padx=(0, 12), pady=10)

        ctk.CTkLabel(bar, text="Category", text_color=MUTED,
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(0, 6))
        self.category_menu = ctk.CTkOptionMenu(bar, variable=self.category_filter_var, values=["All"],
                                               width=150, command=lambda v: self.refresh())
        self.category_menu.pack(side="left", padx=(0, 12))

        ctk.CTkCheckBox(bar, text="⚠️ Low stock only", variable=self.low_stock_only_var,
                        text_color=TEXT, command=self.refresh).pack(side="left", padx=8)

        ctk.CTkButton(bar, text="📥 Export CSV", width=120, fg_color=GREEN, hover_color=GREEN_HOVER,
                      command=self.export_csv).pack(side="right", padx=(6, 14))
        ctk.CTkButton(bar, text="🔄 Reset", width=90, fg_color=GRAY, hover_color=GRAY_HOVER,
                      command=self.reset_filters).pack(side="right", padx=6)

    def build_main(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=3, column=0, sticky="nsew", padx=20, pady=(4, 6))
        main.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        # ---- form panel ----
        form = ctk.CTkFrame(main, corner_radius=14, fg_color=CARD_BG, width=280)
        form.grid(row=0, column=0, sticky="ns", padx=(0, 12))
        form.pack_propagate(False)

        # Bottom widgets are packed FIRST so the buttons are always visible,
        # no matter how short the window is.
        adj = ctk.CTkFrame(form, fg_color="transparent")
        adj.pack(side="bottom", fill="x", padx=12, pady=(0, 12))
        adj.columnconfigure((0, 1), weight=1)
        ctk.CTkButton(adj, text="➕ +1", height=32,
                      command=lambda: self.adjust_stock(1)).grid(row=0, column=0, padx=4, sticky="ew")
        ctk.CTkButton(adj, text="➖ -1", height=32,
                      command=lambda: self.adjust_stock(-1)).grid(row=0, column=1, padx=4, sticky="ew")

        ctk.CTkLabel(form, text="Quick stock adjust", text_color=MUTED,
                     font=ctk.CTkFont(size=12)).pack(side="bottom", anchor="w", padx=16, pady=(8, 2))

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.pack(side="bottom", fill="x", padx=12, pady=(6, 0))
        btns.columnconfigure((0, 1), weight=1)
        ctk.CTkButton(btns, text="➕ Add", height=34, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                      command=self.add).grid(row=0, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(btns, text="✏️ Update", height=34, fg_color=GREEN, hover_color=GREEN_HOVER,
                      command=self.update).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(btns, text="🗑️ Delete", height=34, fg_color=RED, hover_color=RED_HOVER,
                      command=self.delete).grid(row=1, column=0, padx=4, pady=4, sticky="ew")
        ctk.CTkButton(btns, text="🧹 Clear", height=34, fg_color=GRAY, hover_color=GRAY_HOVER,
                      command=self.clear_form).grid(row=1, column=1, padx=4, pady=4, sticky="ew")

        # Fields live in a scrollable area: if the window is small they scroll
        # instead of being cut off.
        fields = ctk.CTkScrollableFrame(form, fg_color="transparent", corner_radius=0)
        fields.pack(side="top", fill="both", expand=True, padx=(6, 2), pady=(8, 0))

        ctk.CTkLabel(fields, text="Item details", text_color=TEXT,
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=10, pady=(4, 2))

        def field(label, widget):
            ctk.CTkLabel(fields, text=label, text_color=MUTED,
                         font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(8, 0))
            widget.pack(fill="x", padx=10, pady=(2, 0))

        field("Item name *", ctk.CTkEntry(fields, textvariable=self.name_var))
        self.form_cat_cb = ctk.CTkComboBox(fields, variable=self.category_var, values=[])
        field("Category", self.form_cat_cb)
        field("Quantity", ctk.CTkEntry(fields, textvariable=self.qty_var))
        field("Unit price ($)", ctk.CTkEntry(fields, textvariable=self.price_var))

        # ---- table panel ----
        table_card = ctk.CTkFrame(main, corner_radius=14, fg_color=CARD_BG)
        table_card.grid(row=0, column=1, sticky="nsew")
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        cols = ("id", "name", "category", "quantity", "price", "total_val", "status")
        self.tree = ttk.Treeview(table_card, columns=cols, show="headings",
                                 selectmode="browse", style="Inventory.Treeview")
        headings = {"id": "ID", "name": "Item name", "category": "Category", "quantity": "Qty",
                    "price": "Price", "total_val": "Total value", "status": "Status"}
        widths = {"id": 55, "name": 260, "category": 150, "quantity": 70, "price": 100,
                  "total_val": 130, "status": 150}
        anchors = {"id": "center", "name": "w", "category": "w", "quantity": "center",
                   "price": "e", "total_val": "e", "status": "center"}
        for c in cols:
            self.tree.heading(c, text=headings[c], command=lambda _c=c: self.sort_by_column(_c, False))
            self.tree.column(c, width=widths[c], anchor=anchors[c], stretch=(c == "name"))

        sy = ctk.CTkScrollbar(table_card, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sy.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        sy.grid(row=0, column=1, sticky="ns", padx=(4, 8), pady=10)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def build_status_bar(self):
        self.status = ctk.CTkLabel(self, text="Ready", anchor="w", text_color=MUTED)
        self.status.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 10))

    # ---------- THEME ----------
    def apply_tree_style(self):
        c = TREE_COLORS["Dark" if ctk.get_appearance_mode() == "Dark" else "Light"]
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Inventory.Treeview", background=c["bg"], foreground=c["fg"],
                        fieldbackground=c["bg"], rowheight=38, borderwidth=0, font=("Segoe UI", 12))
        style.configure("Inventory.Treeview.Heading", background=c["head"], foreground=c["fg"],
                        font=("Segoe UI", 11, "bold"), relief="flat", padding=(8, 8))
        style.map("Inventory.Treeview", background=[("selected", ACCENT)],
                  foreground=[("selected", "#FFFFFF")])
        style.map("Inventory.Treeview.Heading", background=[("active", c["head"])])
        self.tree.tag_configure("even_row", background=c["bg"])
        self.tree.tag_configure("odd_row", background=c["odd"])
        self.tree.tag_configure("low_stock", background=c["low_bg"], foreground=c["low_fg"])
        self.tree.tag_configure("out_stock", background=c["out_bg"], foreground=c["out_fg"])

    def toggle_mode(self):
        new_mode = "light" if ctk.get_appearance_mode() == "Dark" else "dark"
        ctk.set_appearance_mode(new_mode)
        self.apply_tree_style()

    # ---------- DATA ----------
    def refresh_categories(self):
        cats = db.get_categories()
        self.category_menu.configure(values=["All"] + cats)
        if self.category_filter_var.get() not in ["All"] + cats:
            self.category_filter_var.set("All")
        self.form_cat_cb.configure(values=cats)

    def reset_filters(self):
        self.search_var.set("")
        self.category_filter_var.set("All")
        self.low_stock_only_var.set(False)
        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        search = self.search_var.get().strip()
        cat = self.category_filter_var.get()
        low_only = self.low_stock_only_var.get()
        items = db.get_items(search=search, category=cat, low_stock_only=low_only,
                             low_stock_limit=LOW_STOCK_THRESHOLD)

        reselect = None
        for i, (item_id, name, category, qty, price) in enumerate(items):
            if qty == 0:
                status, tag = "❌ Out of stock", ("out_stock",)
            elif qty <= LOW_STOCK_THRESHOLD:
                status, tag = "⚠️ Low stock", ("low_stock",)
            else:
                status, tag = "✅ In stock", ("even_row",) if i % 2 == 0 else ("odd_row",)
            iid = str(item_id)
            self.tree.insert("", "end", iid=iid, tags=tag, values=(
                item_id, name, category or "-", qty, f"${price:.2f}", f"${qty * price:,.2f}", status))
            if self.selected_id is not None and str(self.selected_id) == iid:
                reselect = iid

        if reselect:
            self.tree.selection_set(reselect)

        s = db.get_stats(low_stock_limit=LOW_STOCK_THRESHOLD)
        self.card_vars["products"].set(f"{s['total_products']:,}")
        self.card_vars["units"].set(f"{s['total_units']:,}")
        self.card_vars["value"].set(f"${s['total_value']:,.2f}")
        self.card_vars["low"].set(f"{s['low_stock_count']:,}")
        self.status.configure(text=f"Showing {len(items)} items  |  Low stock threshold: {LOW_STOCK_THRESHOLD} units")

    def read_form(self):
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("Missing field", "Item name is required.")
            return None
        try:
            qty = int(self.qty_var.get().strip() or 0)
            price = float(self.price_var.get().strip().replace("$", "").replace(",", "") or 0)
            if qty < 0 or price < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid input",
                                   "Quantity must be a whole number and price a number (both 0 or more).")
            return None
        return name, self.category_var.get().strip(), qty, price

    def clear_form(self):
        self.selected_id = None
        for v in (self.name_var, self.category_var, self.qty_var, self.price_var):
            v.set("")
        self.tree.selection_remove(self.tree.selection())

    # ---------- ACTIONS ----------
    def on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        item_id, name, cat, qty, price = self.tree.item(sel[0])["values"][:5]
        self.selected_id = int(item_id)
        self.name_var.set(str(name))
        self.category_var.set("" if cat == "-" else str(cat))
        self.qty_var.set(str(qty))
        self.price_var.set(str(price).replace("$", "").replace(",", ""))

    def add(self):
        data = self.read_form()
        if data:
            db.add_item(*data)
            self.clear_form()
            self.refresh_categories()
            self.refresh()
            self.status.configure(text=f"✅ Added '{data[0]}'")

    def update(self):
        if self.selected_id is None:
            messagebox.showinfo("Select item", "Click an item in the table first.")
            return
        data = self.read_form()
        if data:
            db.update_item(self.selected_id, *data)
            self.refresh_categories()
            self.refresh()
            self.status.configure(text=f"✏️ Updated item #{self.selected_id}")

    def delete(self):
        if self.selected_id is None:
            messagebox.showinfo("Select item", "Click an item in the table first.")
            return
        if messagebox.askyesno("Confirm", f"Delete item #{self.selected_id}?"):
            deleted = self.selected_id
            db.delete_item(deleted)
            self.clear_form()
            self.refresh_categories()
            self.refresh()
            self.status.configure(text=f"🗑️ Deleted item #{deleted}")

    def adjust_stock(self, delta):
        if self.selected_id is None:
            messagebox.showinfo("Select item", "Click an item in the table first.")
            return
        db.adjust_quantity(self.selected_id, delta)
        self.refresh()

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
                                            initialfile="inventory_report.csv")
        if path:
            try:
                db.export_to_csv(path)
                messagebox.showinfo("Exported", f"Saved to:\n{path}")
                self.status.configure(text=f"📥 Exported {os.path.basename(path)}")
            except Exception as e:
                messagebox.showerror("Export error", str(e))

    def sort_by_column(self, col, reverse):
        rows = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        try:
            rows.sort(key=lambda t: float(t[0].replace("$", "").replace(",", "")), reverse=reverse)
        except ValueError:
            rows.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for index, (_v, k) in enumerate(rows):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda _c=col: self.sort_by_column(_c, not reverse))