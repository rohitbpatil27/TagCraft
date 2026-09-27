"""
TagCraft - Open Source Thermal Barcode Tag Printer
A modern, zero-dependency desktop application for printing retail barcode garment tags
on TVS, TSC, and TSPL-compatible thermal printers directly from CSV/Excel databases.

GitHub: https://github.com/rohitbpatil27/TagCraft
License: MIT
"""

import sys
import os
import json
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from printer import list_installed_printers, detect_barcode_printer, send_raw_tspl
from tspl_engine import generate_tspl_job, clean_label_text, format_price_display

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config() -> dict:
    default_cfg = {
        "store_name": "KAPIL UNIFORMS",
        "printer_name": "",
        "layout": "2-UP (2 across, 50x38mm)",
        "last_csv_path": ""
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_cfg.update(data)
        except Exception:
            pass
    return default_cfg


def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


class TagCraftApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TagCraft - Open Source Thermal Barcode Printer")
        self.root.geometry("1180x740")
        self.root.minsize(980, 600)

        self.config = load_config()
        self.all_items = []
        self.filtered_items = []

        self.setup_ui()
        self.auto_load_printers()
        self.init_data()

    def setup_ui(self):
        # 1. Header Banner
        header = tk.Frame(self.root, bg="#0f172a", height=56)
        header.pack(fill=tk.X, side=tk.TOP)

        title_box = tk.Frame(header, bg="#0f172a")
        title_box.pack(side=tk.LEFT, padx=16, pady=8)

        tk.Label(title_box, text="🏷️ TagCraft", font=("Segoe UI", 15, "bold"), fg="#38bdf8", bg="#0f172a").pack(side=tk.LEFT)
        tk.Label(title_box, text=" | Retail Barcode Tag Studio", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a").pack(side=tk.LEFT, padx=4)

        # Store Name Header Configuration (Editable in place!)
        store_frame = tk.Frame(header, bg="#0f172a")
        store_frame.pack(side=tk.RIGHT, padx=16, pady=8)

        tk.Label(store_frame, text="Store:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg="#0f172a").pack(side=tk.LEFT, padx=(4, 2))
        self.store_name_var = tk.StringVar(value=self.config.get("store_name", "KAPIL UNIFORMS"))
        self.store_entry = tk.Entry(store_frame, textvariable=self.store_name_var, font=("Segoe UI", 9, "bold"), 
                                    width=16, bg="#1e293b", fg="#f8fafc", insertbackground="white", relief=tk.FLAT)
        self.store_entry.pack(side=tk.LEFT, padx=3, ipady=3)
        self.store_name_var.trace_add("write", lambda *_: self.on_store_name_changed())

        tk.Label(store_frame, text="Contact:", font=("Segoe UI", 9, "bold"), fg="#e2e8f0", bg="#0f172a").pack(side=tk.LEFT, padx=(10, 2))
        self.contact_info_var = tk.StringVar(value=self.config.get("contact_info", "Vijayapura Ph:9880333885"))
        self.contact_entry = tk.Entry(store_frame, textvariable=self.contact_info_var, font=("Segoe UI", 9), 
                                      width=24, bg="#1e293b", fg="#f8fafc", insertbackground="white", relief=tk.FLAT)
        self.contact_entry.pack(side=tk.LEFT, padx=3, ipady=3)
        self.contact_info_var.trace_add("write", lambda *_: self.on_contact_info_changed())

        # 2. Main Control Bar (File Loader, Printer, Layout)
        control_card = tk.LabelFrame(self.root, text=" Device & Source Configuration ", font=("Segoe UI", 9, "bold"), padx=10, pady=8)
        control_card.pack(fill=tk.X, padx=14, pady=8)

        # Open File Button
        open_btn = tk.Button(control_card, text="📂 Load CSV File...", font=("Segoe UI", 9, "bold"), 
                             bg="#e0f2fe", fg="#0369a1", relief=tk.GROOVE, padx=10, pady=3, command=self.browse_csv_file)
        open_btn.grid(row=0, column=0, sticky=tk.W, padx=4, pady=2)

        self.file_label = tk.Label(control_card, text="No file loaded", font=("Segoe UI", 8, "italic"), fg="#64748b")
        self.file_label.grid(row=0, column=1, sticky=tk.W, padx=4, pady=2)

        # Printer Selector
        tk.Label(control_card, text="Target Printer:").grid(row=0, column=2, sticky=tk.W, padx=(20, 4), pady=2)
        self.printer_var = tk.StringVar()
        self.printer_combo = ttk.Combobox(control_card, textvariable=self.printer_var, state="readonly", width=26)
        self.printer_combo.grid(row=0, column=3, sticky=tk.W, padx=4, pady=2)
        self.printer_combo.bind("<<ComboboxSelected>>", lambda _: self.on_printer_selected())

        refresh_btn = ttk.Button(control_card, text="🔄", width=3, command=self.auto_load_printers)
        refresh_btn.grid(row=0, column=4, sticky=tk.W, padx=2, pady=2)

        # Roll Layout Selector
        tk.Label(control_card, text="Roll Format:").grid(row=0, column=5, sticky=tk.W, padx=(20, 4), pady=2)
        self.layout_var = tk.StringVar(value=self.config.get("layout", "2-UP (2 across, 50x38mm)"))
        self.layout_combo = ttk.Combobox(control_card, textvariable=self.layout_var, state="readonly", width=24,
                                         values=["2-UP (2 across, 50x38mm)", "1-UP (Single, 50x38mm)"])
        self.layout_combo.grid(row=0, column=6, sticky=tk.W, padx=4, pady=2)
        self.layout_combo.bind("<<ComboboxSelected>>", lambda _: self.on_layout_changed())

        # 3. Filter Bar (Category / Search)
        filter_bar = tk.Frame(self.root, padx=14, pady=4)
        filter_bar.pack(fill=tk.X)

        tk.Label(filter_bar, text="Category / Group:").pack(side=tk.LEFT, padx=(0, 4))
        self.category_var = tk.StringVar(value="All Categories")
        self.category_combo = ttk.Combobox(filter_bar, textvariable=self.category_var, state="readonly", width=22)
        self.category_combo.pack(side=tk.LEFT, padx=4)
        self.category_combo.bind("<<ComboboxSelected>>", lambda _: self.apply_filter())

        tk.Label(filter_bar, text="🔍 Search Item / Size:").pack(side=tk.LEFT, padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(filter_bar, textvariable=self.search_var, width=28)
        self.search_entry.pack(side=tk.LEFT, padx=4)
        self.search_var.trace_add("write", lambda *_: self.apply_filter())

        # 4. Middle Content: Table + Live Tag Preview Canvas
        middle_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        middle_paned.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

        # Table Frame
        table_frame = tk.Frame(middle_paned)
        middle_paned.add(table_frame, weight=3)

        columns = ("group", "name", "size", "price", "barcode", "copies")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("group", text="Category / School")
        self.tree.heading("name", text="Item Description")
        self.tree.heading("size", text="Size")
        self.tree.heading("price", text="Price / MRP")
        self.tree.heading("barcode", text="Barcode SKU")
        self.tree.heading("copies", text="Copies")

        self.tree.column("group", width=140, anchor=tk.W)
        self.tree.column("name", width=300, anchor=tk.W)
        self.tree.column("size", width=60, anchor=tk.CENTER)
        self.tree.column("price", width=90, anchor=tk.E)
        self.tree.column("barcode", width=110, anchor=tk.CENTER)
        self.tree.column("copies", width=60, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", lambda _: self.update_live_preview())
        self.tree.bind("<Double-1>", self.on_double_click_row)

        # Preview Frame (Right side)
        preview_frame = tk.LabelFrame(middle_paned, text=" Live Tag Preview ", font=("Segoe UI", 9, "bold"), padx=10, pady=10)
        middle_paned.add(preview_frame, weight=1)

        self.preview_canvas = tk.Canvas(preview_frame, width=240, height=180, bg="#ffffff", highlightthickness=1, highlightbackground="#cbd5e1")
        self.preview_canvas.pack(pady=10)

        preview_info = tk.Label(preview_frame, text="Real-time 50mm × 38mm Tag Mockup\nMatches printer thermal output", 
                                font=("Segoe UI", 8), fg="#64748b", justify=tk.CENTER)
        preview_info.pack(pady=4)

        # 5. Bottom Controls Bar
        bottom_bar = tk.Frame(self.root, padx=14, pady=10)
        bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.count_label = tk.Label(bottom_bar, text="Showing 0 items", font=("Segoe UI", 9, "italic"), fg="#475569")
        self.count_label.pack(side=tk.LEFT, padx=4)

        ttk.Button(bottom_bar, text="Select All", command=self.select_all).pack(side=tk.LEFT, padx=4)
        ttk.Button(bottom_bar, text="Deselect All", command=self.deselect_all).pack(side=tk.LEFT, padx=4)

        # Quick Copies Setters
        tk.Label(bottom_bar, text="Set Copies:").pack(side=tk.LEFT, padx=(16, 2))
        ttk.Button(bottom_bar, text="2", width=3, command=lambda: self.set_selected_copies(2)).pack(side=tk.LEFT, padx=1)
        ttk.Button(bottom_bar, text="4", width=3, command=lambda: self.set_selected_copies(4)).pack(side=tk.LEFT, padx=1)
        ttk.Button(bottom_bar, text="10", width=3, command=lambda: self.set_selected_copies(10)).pack(side=tk.LEFT, padx=1)
        ttk.Button(bottom_bar, text="20", width=3, command=lambda: self.set_selected_copies(20)).pack(side=tk.LEFT, padx=1)

        # Print Buttons
        self.batch_btn = tk.Button(bottom_bar, text="🖨️ Print Selected (Batch)", bg="#0284c7", fg="white", 
                                   font=("Segoe UI", 10, "bold"), padx=14, pady=5, relief=tk.RAISED, command=self.print_batch)
        self.batch_btn.pack(side=tk.RIGHT, padx=4)

        self.test_btn = tk.Button(bottom_bar, text="🧪 Print 1 Test Row", bg="#16a34a", fg="white", 
                                  font=("Segoe UI", 10, "bold"), padx=14, pady=5, relief=tk.RAISED, command=self.print_test_row)
        self.test_btn.pack(side=tk.RIGHT, padx=4)

    # ----------------- LOGIC & HELPERS -----------------
    def auto_load_printers(self):
        printers = list_installed_printers()
        self.printer_combo["values"] = printers
        saved_printer = self.config.get("printer_name", "")

        if saved_printer in printers:
            self.printer_var.set(saved_printer)
        else:
            detected = detect_barcode_printer(printers)
            if detected:
                self.printer_var.set(detected)
                self.config["printer_name"] = detected
                save_config(self.config)
            elif printers:
                self.printer_var.set(printers[0])

    def on_printer_selected(self):
        self.config["printer_name"] = self.printer_var.get()
        save_config(self.config)

    def on_store_name_changed(self):
        self.config["store_name"] = self.store_name_var.get()
        save_config(self.config)
        self.update_live_preview()

    def on_contact_info_changed(self):
        self.config["contact_info"] = self.contact_info_var.get()
        save_config(self.config)
        self.update_live_preview()

    def on_layout_changed(self):
        self.config["layout"] = self.layout_var.get()
        save_config(self.config)

    def browse_csv_file(self):
        chosen = filedialog.askopenfilename(
            title="Select Inventory CSV File",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if chosen:
            self.load_csv(chosen)

    def init_data(self):
        last_csv = self.config.get("last_csv_path", "")
        if last_csv and os.path.exists(last_csv):
            self.load_csv(last_csv)
        else:
            # Fallback to sample data
            sample = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data", "sample_inventory.csv")
            if os.path.exists(sample):
                self.load_csv(sample)

    def load_csv(self, filepath: str):
        if not os.path.exists(filepath):
            return

        self.all_items = []
        categories = set(["All Categories"])

        try:
            with open(filepath, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames or []

                # Smart column detection
                group_col = next((c for c in headers if c.lower() in ["item group", "category", "group", "school"]), "Item Group")
                name_col = next((c for c in headers if c.lower() in ["item name", "name", "description", "item"]), "Item Name")
                size_col = next((c for c in headers if c.lower() in ["size", "variant"]), "Size")
                price_col = next((c for c in headers if c.lower() in ["selling price", "price", "rate", "mrp"]), "Selling Price")
                barcode_col = next((c for c in headers if c.lower() in ["barcode", "sku", "code"]), "Barcode")

                for row in reader:
                    group = row.get(group_col, "").strip()
                    if group:
                        categories.add(group)
                    
                    self.all_items.append({
                        "group": group,
                        "name": row.get(name_col, "").strip(),
                        "size": row.get(size_col, "").strip(),
                        "price": row.get(price_col, "").strip(),
                        "barcode": row.get(barcode_col, "").strip(),
                        "copies": 2
                    })

            self.config["last_csv_path"] = filepath
            save_config(self.config)

            self.file_label.config(text=os.path.basename(filepath), fg="#0f766e")
            self.category_combo["values"] = ["All Categories"] + sorted([c for c in categories if c != "All Categories"])
            self.category_var.set("All Categories")
            self.apply_filter()

        except Exception as e:
            messagebox.showerror("File Error", f"Could not load CSV file:\n{e}")

    def apply_filter(self):
        cat = self.category_var.get()
        q = self.search_var.get().strip().lower()

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.filtered_items = []
        for it in self.all_items:
            if cat != "All Categories" and it["group"] != cat:
                continue
            if q:
                combined = f"{it['group']} {it['name']} {it['size']} {it['barcode']}".lower()
                if q not in combined:
                    continue
            self.filtered_items.append(it)

        for it in self.filtered_items:
            self.tree.insert("", tk.END, values=(
                it["group"], it["name"], it["size"], it["price"], it["barcode"], it["copies"]
            ))

        self.count_label.config(text=f"Showing {len(self.filtered_items)} of {len(self.all_items)} items")
        if self.filtered_items:
            # Select first item by default for preview
            first_child = self.tree.get_children()[0]
            self.tree.selection_set(first_child)
            self.update_live_preview()

    def update_live_preview(self):
        self.preview_canvas.delete("all")
        selected = self.tree.selection()
        if not selected:
            self.preview_canvas.create_text(120, 90, text="Select an item\nto preview tag", fill="#94a3b8", font=("Segoe UI", 10))
            return

        vals = self.tree.item(selected[0], "values")
        store = self.store_name_var.get().strip() or "MY STORE"
        contact = self.contact_info_var.get().strip()
        name = clean_label_text(vals[1], max_chars=25)
        size = vals[2]
        price = format_price_display(vals[3])
        barcode = vals[4]

        # Draw sticker border (simulating rounded 50mm x 38mm sticker)
        self.preview_canvas.create_rectangle(10, 8, 230, 172, outline="#94a3b8", width=1, fill="#ffffff")
        
        if contact:
            # 1. Store Header
            self.preview_canvas.create_text(120, 30, text=store, font=("Segoe UI", 10, "bold"), fill="#0f172a")
            # 2. Contact Sub-header (Shifted slightly left)
            self.preview_canvas.create_text(116, 46, text=contact, font=("Segoe UI", 7, "bold"), fill="#0369a1")
            # 3. Item Name
            self.preview_canvas.create_text(120, 64, text=name, font=("Segoe UI", 8), fill="#334155")
            # 4. Size (Prominent, no rate/MRP)
            size_display = f"Size: {size}" if (size and size not in ["-", "N/A"]) else ""
            if size_display:
                self.preview_canvas.create_text(120, 82, text=size_display, font=("Segoe UI", 9, "bold"), fill="#0f172a")
                # 5. Barcode Stripes Mockup
                start_x = 35
                for i in range(32):
                    w = 2 if (i % 3 == 0 or i % 7 == 0) else 1
                    self.preview_canvas.create_line(start_x + i * 5, 100, start_x + i * 5, 146, width=w, fill="#000000")
                # 6. Barcode Text (Centered below stripes)
                self.preview_canvas.create_text(120, 157, text=barcode, font=("Consolas", 8, "bold"), fill="#0f172a")
            else:
                start_x = 35
                for i in range(32):
                    w = 2 if (i % 3 == 0 or i % 7 == 0) else 1
                    self.preview_canvas.create_line(start_x + i * 5, 86, start_x + i * 5, 142, width=w, fill="#000000")
                self.preview_canvas.create_text(120, 154, text=barcode, font=("Consolas", 8, "bold"), fill="#0f172a")
        else:
            # 1. Store Header
            self.preview_canvas.create_text(120, 36, text=store, font=("Segoe UI", 11, "bold"), fill="#0f172a")
            # 2. Item Name
            self.preview_canvas.create_text(120, 60, text=name, font=("Segoe UI", 9), fill="#334155")
            # 3. Size (No rate/MRP)
            size_display = f"Size: {size}" if (size and size not in ["-", "N/A"]) else ""
            if size_display:
                self.preview_canvas.create_text(120, 82, text=size_display, font=("Segoe UI", 10, "bold"), fill="#0f172a")
                start_x = 35
                for i in range(32):
                    w = 2 if (i % 3 == 0 or i % 7 == 0) else 1
                    self.preview_canvas.create_line(start_x + i * 5, 102, start_x + i * 5, 148, width=w, fill="#000000")
                self.preview_canvas.create_text(120, 158, text=barcode, font=("Consolas", 8, "bold"), fill="#0f172a")
            else:
                start_x = 35
                for i in range(32):
                    w = 2 if (i % 3 == 0 or i % 7 == 0) else 1
                    self.preview_canvas.create_line(start_x + i * 5, 86, start_x + i * 5, 142, width=w, fill="#000000")
                self.preview_canvas.create_text(120, 154, text=barcode, font=("Consolas", 8, "bold"), fill="#0f172a")

    def select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def deselect_all(self):
        self.tree.selection_remove(self.tree.get_children())

    def set_selected_copies(self, qty: int):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Select Items", "Please click on items in the table first.")
            return

        for item_id in selected:
            vals = list(self.tree.item(item_id, "values"))
            vals[5] = qty
            self.tree.item(item_id, values=vals)
            bc = vals[4]
            for it in self.all_items:
                if it["barcode"] == bc:
                    it["copies"] = qty

    def on_double_click_row(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return
        vals = list(self.tree.item(item_id, "values"))
        current = int(vals[5])
        next_qty = 4 if current == 2 else (10 if current == 4 else (20 if current == 10 else 2))
        vals[5] = next_qty
        self.tree.item(item_id, values=vals)
        for it in self.all_items:
            if it["barcode"] == vals[4]:
                it["copies"] = next_qty

    def print_test_row(self):
        selected = self.tree.selection()
        if not selected:
            children = self.tree.get_children()
            if not children:
                messagebox.showwarning("No Items", "No items to print.")
                return
            target_id = children[0]
        else:
            target_id = selected[0]

        vals = self.tree.item(target_id, "values")
        item = {
            "name": vals[1],
            "size": vals[2],
            "price": vals[3],
            "barcode": vals[4]
        }
        store = self.store_name_var.get().strip() or "MY STORE"
        contact = self.contact_info_var.get().strip()
        printer = self.printer_var.get()
        if not printer:
            messagebox.showerror("No Printer", "Please select a target printer.")
            return

        layout = "2-UP" if "2-UP" in self.layout_var.get() else "1-UP"
        items_payload = [item, item] if layout == "2-UP" else [item]

        tspl = generate_tspl_job(items_payload, store_name=store, contact_info=contact, layout=layout)
        ok, msg = send_raw_tspl(printer, tspl, job_name="TagCraft_Test")
        if ok:
            messagebox.showinfo("Test Print Sent", f"Test print successfully sent to:\n{printer}")
        else:
            messagebox.showerror("Print Error", f"Printing failed:\n{msg}")

    def print_batch(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Items", "Please select items from the table to print.")
            return

        queue = []
        for item_id in selected:
            vals = self.tree.item(item_id, "values")
            qty = int(vals[5])
            it = {
                "name": vals[1],
                "size": vals[2],
                "price": vals[3],
                "barcode": vals[4]
            }
            for _ in range(qty):
                queue.append(it)

        total_stickers = len(queue)
        layout = "2-UP" if "2-UP" in self.layout_var.get() else "1-UP"
        rows = (total_stickers + 1) // 2 if layout == "2-UP" else total_stickers

        confirm = messagebox.askyesno(
            "Confirm Print",
            f"You are about to print {total_stickers} tag(s) ({rows} rows).\n\n"
            f"Printer: {self.printer_var.get()}\n"
            f"Layout: {layout}\n\nProceed?"
        )
        if not confirm:
            return

        store = self.store_name_var.get().strip() or "MY STORE"
        contact = self.contact_info_var.get().strip()
        printer = self.printer_var.get()
        tspl = generate_tspl_job(queue, store_name=store, contact_info=contact, layout=layout)
        ok, msg = send_raw_tspl(printer, tspl, job_name="TagCraft_Batch")
        if ok:
            messagebox.showinfo("Batch Complete", f"Successfully sent {total_stickers} tags to {printer}!")
        else:
            messagebox.showerror("Print Error", f"Printing failed:\n{msg}")


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = TagCraftApp(root)
        root.mainloop()
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_debug.log")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(err_msg)
        try:
            from tkinter import messagebox
            messagebox.showerror("TagCraft Error", f"TagCraft encountered an error:\n\n{e}\n\nDetails saved to crash_debug.log")
        except Exception:
            pass
