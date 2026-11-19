from __future__ import annotations
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
from typing import List
from core.organizer import FileOrganizer, PlanItem
from core.hasher import find_duplicates

class NeatFilesApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NeatFiles - Clean File Organizer")
        self.geometry("980x640")
        self.minsize(800, 500)

        self.organizer = FileOrganizer()
        self.current_plan: List[PlanItem] = []
        self.last_manifest: Path | None = None

        self._apply_styles()
        self._build_ui()

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#F5F6F8")
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), background="#F5F6F8", foreground="#1F2937")
        style.configure("Sub.TLabel", font=("Segoe UI", 9), background="#F5F6F8", foreground="#4B5563")
        style.configure("Card.TFrame", background="#FFFFFF", relief="solid", borderwidth=1)
        style.configure("Action.TButton", font=("Segoe UI", 9, "bold"), background="#2563EB", foreground="#FFFFFF")
        style.map("Action.TButton", background=[("active", "#1D4ED8")])
        self.configure(bg="#F5F6F8")

    def _build_ui(self):
        # Header
        header_frame = ttk.Frame(self, padding="16 12 16 8")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="NeatFiles Organizer", style="Header.TLabel").pack(anchor="w")
        ttk.Label(header_frame, text="Safely classify, group, and organize messy directories", style="Sub.TLabel").pack(anchor="w")

        # Control Settings Bar
        ctrl_frame = ttk.Frame(self, padding="16 4 16 10")
        ctrl_frame.pack(fill=tk.X)

        # Source Selection
        ttk.Label(ctrl_frame, text="Source:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.src_var = tk.StringVar(value=str(Path.home() / "Downloads"))
        ttk.Entry(ctrl_frame, textvariable=self.src_var, width=32).grid(row=0, column=1, padx=4)
        ttk.Button(ctrl_frame, text="Browse", command=self._browse_source).grid(row=0, column=2, padx=4)

        # Target Selection
        ttk.Label(ctrl_frame, text="Target (Opt):", font=("Segoe UI", 9, "bold")).grid(row=0, column=3, sticky="w", padx=(12, 4))
        self.dest_var = tk.StringVar(value="")
        ttk.Entry(ctrl_frame, textvariable=self.dest_var, width=28).grid(row=0, column=4, padx=4)
        ttk.Button(ctrl_frame, text="Browse", command=self._browse_target).grid(row=0, column=5, padx=4)

        # Modes & Options
        opt_frame = ttk.Frame(self, padding="16 0 16 10")
        opt_frame.pack(fill=tk.X)

        ttk.Label(opt_frame, text="Group By:").grid(row=0, column=0, sticky="w")
        self.mode_var = tk.StringVar(value="category")
        mode_combo = ttk.Combobox(opt_frame, textvariable=self.mode_var, values=["category", "date", "extension"], width=12, state="readonly")
        mode_combo.grid(row=0, column=1, padx=6)

        ttk.Label(opt_frame, text="Collision:").grid(row=0, column=2, sticky="w", padx=(10, 0))
        self.conflict_var = tk.StringVar(value="rename")
        conflict_combo = ttk.Combobox(opt_frame, textvariable=self.conflict_var, values=["rename", "skip", "overwrite"], width=10, state="readonly")
        conflict_combo.grid(row=0, column=3, padx=6)

        self.copy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Copy instead of Move", variable=self.copy_var).grid(row=0, column=4, padx=10)

        self.recurse_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_frame, text="Include Subfolders", variable=self.recurse_var).grid(row=0, column=5, padx=10)

        # Action Buttons
        ttk.Button(opt_frame, text="1. Scan & Preview", command=self._start_scan).grid(row=0, column=6, padx=(12, 4))
        self.exec_btn = ttk.Button(opt_frame, text="2. Organize Files", style="Action.TButton", command=self._start_organize, state="disabled")
        self.exec_btn.grid(row=0, column=7, padx=4)
        self.undo_btn = ttk.Button(opt_frame, text="Undo Rollback", command=self._start_undo, state="disabled")
        self.undo_btn.grid(row=0, column=8, padx=4)

        # Treeview Preview Area
        table_frame = ttk.Frame(self, padding="16 0 16 8")
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("File Name", "Category / Folder", "Size", "Target Path")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        self.tree.heading("File Name", text="File Name")
        self.tree.heading("Category / Folder", text="Category / Folder")
        self.tree.heading("Size", text="Size (KB)")
        self.tree.heading("Target Path", text="Target Path")

        self.tree.column("File Name", width=200, anchor="w")
        self.tree.column("Category / Folder", width=140, anchor="center")
        self.tree.column("Size", width=90, anchor="e")
        self.tree.column("Target Path", width=420, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom Status Bar & Progress
        status_frame = ttk.Frame(self, padding="16 6 16 10")
        status_frame.pack(fill=tk.X)
        self.progress = ttk.Progressbar(status_frame, orient="horizontal", mode="determinate")
        self.progress.pack(fill=tk.X, pady=(0, 4))
        self.status_var = tk.StringVar(value="Ready. Select a folder to begin scanning.")
        ttk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 9)).pack(anchor="w")

    def _browse_source(self):
        folder = filedialog.askdirectory(title="Select Source Directory")
        if folder:
            self.src_var.set(folder)

    def _browse_target(self):
        folder = filedialog.askdirectory(title="Select Target Directory (Optional)")
        if folder:
            self.dest_var.set(folder)

    def _start_scan(self):
        src = Path(self.src_var.get())
        if not src.is_dir():
            messagebox.showerror("Invalid Directory", "Please provide a valid source folder.")
            return

        self.status_var.set("Scanning files...")
        self.tree.delete(*self.tree.get_children())

        def worker():
            target = Path(self.dest_var.get()) if self.dest_var.get().strip() else None
            try:
                plan = self.organizer.build_plan(
                    src, target, mode=self.mode_var.get(), recursive=self.recurse_var.get()
                )
                self.after(0, self._populate_preview, plan)
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Scan failed: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    def _populate_preview(self, plan: List[PlanItem]):
        self.current_plan = plan
        for item in plan:
            size_kb = f"{item.size / 1024:.1f}"
            self.tree.insert("", tk.END, values=(item.src.name, item.category, size_kb, str(item.dest)))
        self.status_var.set(f"Found {len(plan)} files ready to organize.")
        self.exec_btn.configure(state="normal" if plan else "disabled")

    def _start_organize(self):
        if not self.current_plan:
            return
        if not messagebox.askyesno("Confirm", f"Proceed with organizing {len(self.current_plan)} files?"):
            return

        self.exec_btn.configure(state="disabled")
        self.progress["maximum"] = len(self.current_plan)
        self.progress["value"] = 0

        def progress_cb(current, total, filename):
            self.after(0, lambda: (self.progress.configure(value=current),
                                   self.status_var.set(f"Processing ({current}/{total}): {filename}")))

        def worker():
            try:
                count, manifest = self.organizer.execute_plan(
                    self.current_plan,
                    copy_mode=self.copy_var.get(),
                    conflict_strategy=self.conflict_var.get(),
                    progress_cb=progress_cb
                )
                self.last_manifest = manifest
                self.after(0, lambda: self._on_finish_organize(count, manifest))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Organization Failed", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_finish_organize(self, count: int, manifest: Path):
        self.status_var.set(f"Completed! Organized {count} files. Manifest saved.")
        self.undo_btn.configure(state="normal")
        self.tree.delete(*self.tree.get_children())
        self.current_plan = []
        messagebox.showinfo("Success", f"Organized {count} files successfully.\nTransaction log: {manifest.name}")

    def _start_undo(self):
        manifest = self.last_manifest
        if not manifest or not manifest.exists():
            selected = filedialog.askopenfilename(title="Select Transaction Manifest", filetypes=[("JSON Files", "*.json")])
            if not selected:
                return
            manifest = Path(selected)

        if not messagebox.askyesno("Confirm Undo", f"Revert operations from manifest:\n{manifest.name}?"):
            return

        try:
            restored = self.organizer.rollback(manifest)
            self.status_var.set(f"Rollback complete! Restored {restored} operations.")
            messagebox.showinfo("Rollback Complete", f"Restored {restored} files to original locations.")
            self.undo_btn.configure(state="disabled")
        except Exception as e:
            messagebox.showerror("Rollback Error", str(e))
