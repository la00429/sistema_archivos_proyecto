import os
import sys
import time
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional

from .manager import FSManager
from .metadata import FileMetadata
from .permissions import FilePermissions

# Try to enable high DPI awareness on Windows to prevent blurry GUI
if sys.platform == 'win32':
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

def format_size(bytes_size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}" if unit != 'B' else f"{bytes_size} B"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"

def format_time(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

class FileEditorWindow(tk.Toplevel):
    """
    Built-in Text Editor / Hex Viewer dialog.
    Automatically detects file type (text vs binary) and presents an editor or viewer.
    """
    def __init__(self, parent, filepath: str):
        super().__init__(parent)
        self.filepath = os.path.abspath(filepath)
        self.filename = os.path.basename(filepath)
        self.title(f"Editor - {self.filename}")
        self.geometry("800x600")
        self.configure(bg='#1e1e1e')
        
        # Read contents
        try:
            self.content = FSManager.read_file(self.filepath)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo leer el archivo: {e}")
            self.destroy()
            return

        # Determine type
        from .utils import detect_file_type, detect_encoding
        self.file_type = detect_file_type(self.filepath)
        self.encoding = detect_encoding(self.filepath)

        self.setup_ui()

    def setup_ui(self):
        # Header Info
        header_frame = tk.Frame(self, bg='#2d2d2d', height=40)
        header_frame.pack(fill=tk.X)
        
        type_lbl = tk.Label(
            header_frame, 
            text=f"Archivo: {self.filename} | Tipo: {self.file_type.upper()} | Codificación: {self.encoding.upper()}", 
            bg='#2d2d2d', 
            fg='#ffffff',
            font=('Segoe UI', 10, 'bold')
        )
        type_lbl.pack(side=tk.LEFT, padx=10, pady=10)

        # Content Text Area
        self.txt_area = tk.Text(
            self, 
            bg='#1e1e1e', 
            fg='#ffffff', 
            insertbackground='white',
            font=('Consolas', 11),
            wrap=tk.WORD if self.file_type == 'text' else tk.NONE,
            padx=10,
            pady=10,
            bd=0
        )
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.txt_area.yview)
        self.txt_area.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_area.pack(fill=tk.BOTH, expand=True)

        # Load content
        if self.file_type == 'binary':
            # View-only Hexdump
            from .cli import hex_dump
            self.txt_area.insert(tk.END, hex_dump(self.content))
            self.txt_area.configure(state=tk.DISABLED)
            
            # Bottom action bar (close only)
            btn_frame = tk.Frame(self, bg='#2d2d2d')
            btn_frame.pack(fill=tk.X)
            close_btn = ttk.Button(btn_frame, text="Cerrar", command=self.destroy)
            close_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        else:
            # Edit text mode
            self.txt_area.insert(tk.END, self.content)
            
            # Bottom action bar (Save/Cancel)
            btn_frame = tk.Frame(self, bg='#2d2d2d')
            btn_frame.pack(fill=tk.X)
            
            save_btn = ttk.Button(btn_frame, text="Guardar", command=self.save_file)
            save_btn.pack(side=tk.RIGHT, padx=10, pady=10)
            
            cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=self.destroy)
            cancel_btn.pack(side=tk.RIGHT, padx=5, pady=10)

    def save_file(self):
        new_content = self.txt_area.get("1.0", tk.END)
        # Remove trailing newline added by tkinter Text widget
        if new_content.endswith('\n'):
            new_content = new_content[:-1]
            
        try:
            FSManager.write_file(self.filepath, new_content, encoding=self.encoding)
            messagebox.showinfo("Guardado", f"El archivo '{self.filename}' se guardó correctamente.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")


class EditTimesDialog(tk.Toplevel):
    """
    Dialog to edit atime, mtime, and birthtime metadata.
    """
    def __init__(self, parent, filepath: str, meta: FileMetadata, on_save_callback):
        super().__init__(parent)
        self.filepath = filepath
        self.meta = meta
        self.on_save = on_save_callback
        
        self.title("Modificar Marcas de Tiempo")
        self.geometry("450x250")
        self.resizable(False, False)
        self.configure(bg='#1e1e1e')
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

    def format_ts(self, ts) -> str:
        if not ts:
            return ""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

    def parse_time_str(self, time_str: str) -> Optional[float]:
        time_str = time_str.strip()
        if not time_str:
            return None
        try:
            struct = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return time.mktime(struct)
        except ValueError:
            raise ValueError(f"Formato incorrecto para '{time_str}'. Usar YYYY-MM-DD HH:MM:SS")

    def setup_ui(self):
        # Header Label
        lbl = tk.Label(self, text="Editar marcas de tiempo", font=('Segoe UI', 12, 'bold'), bg='#1e1e1e', fg='#ffffff')
        lbl.pack(pady=10)

        grid_frame = tk.Frame(self, bg='#1e1e1e')
        grid_frame.pack(padx=20, fill=tk.X)

        # Atime
        tk.Label(grid_frame, text="Acceso (atime):", bg='#1e1e1e', fg='#ffffff').grid(row=0, column=0, sticky='w', pady=5)
        self.entry_atime = ttk.Entry(grid_frame, width=30)
        self.entry_atime.insert(0, self.format_ts(self.meta.atime))
        self.entry_atime.grid(row=0, column=1, pady=5, padx=10)

        # Mtime
        tk.Label(grid_frame, text="Modificación (mtime):", bg='#1e1e1e', fg='#ffffff').grid(row=1, column=0, sticky='w', pady=5)
        self.entry_mtime = ttk.Entry(grid_frame, width=30)
        self.entry_mtime.insert(0, self.format_ts(self.meta.mtime))
        self.entry_mtime.grid(row=1, column=1, pady=5, padx=10)

        # Birthtime (Only editable on Windows)
        tk.Label(grid_frame, text="Creación (birthtime):", bg='#1e1e1e', fg='#ffffff').grid(row=2, column=0, sticky='w', pady=5)
        self.entry_birth = ttk.Entry(grid_frame, width=30)
        if self.meta.birthtime:
            self.entry_birth.insert(0, self.format_ts(self.meta.birthtime))
        else:
            self.entry_birth.insert(0, "No soportado en este S.O.")
            self.entry_birth.configure(state=tk.DISABLED)
        self.entry_birth.grid(row=2, column=1, pady=5, padx=10)

        # Buttons
        btn_frame = tk.Frame(self, bg='#1e1e1e')
        btn_frame.pack(pady=20, side=tk.BOTTOM, fill=tk.X)

        save_btn = ttk.Button(btn_frame, text="Guardar", command=self.save)
        save_btn.pack(side=tk.RIGHT, padx=20)

        cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def save(self):
        try:
            atime = self.parse_time_str(self.entry_atime.get())
            mtime = self.parse_time_str(self.entry_mtime.get())
            birthtime = None
            if self.meta.birthtime and self.entry_birth.get().strip():
                birthtime = self.parse_time_str(self.entry_birth.get())

            FSManager.set_times(self.filepath, atime=atime, mtime=mtime, birthtime=birthtime)
            self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar marcas de tiempo:\n{e}")


class CreateLinkDialog(tk.Toplevel):
    """
    Dialog to create links (hard links, symbolic links, directory junctions).
    """
    def __init__(self, parent, target_path: str, on_create_callback):
        super().__init__(parent)
        self.target_path = os.path.abspath(target_path)
        self.on_create = on_create_callback
        
        self.title("Crear Enlace / Link")
        self.geometry("500x230")
        self.resizable(False, False)
        self.configure(bg='#1e1e1e')
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        # Header Label
        lbl = tk.Label(self, text="Crear nuevo enlace (Link)", font=('Segoe UI', 12, 'bold'), bg='#1e1e1e', fg='#ffffff')
        lbl.pack(pady=10)

        grid_frame = tk.Frame(self, bg='#1e1e1e')
        grid_frame.pack(padx=20, fill=tk.X)

        # Target (readonly)
        tk.Label(grid_frame, text="Destino (Target):", bg='#1e1e1e', fg='#ffffff').grid(row=0, column=0, sticky='w', pady=5)
        lbl_target = tk.Label(grid_frame, text=self.target_path, fg='#007acc', bg='#1e1e1e', anchor='w', justify='left')
        lbl_target.grid(row=0, column=1, pady=5, padx=10, sticky='w')

        # Link Type
        tk.Label(grid_frame, text="Tipo de Enlace:", bg='#1e1e1e', fg='#ffffff').grid(row=1, column=0, sticky='w', pady=5)
        self.link_type_var = tk.StringVar(value="symlink")
        
        radio_frame = tk.Frame(grid_frame, bg='#1e1e1e')
        radio_frame.grid(row=1, column=1, pady=5, padx=10, sticky='w')
        
        ttk.Radiobutton(radio_frame, text="Simbólico (Symlink)", variable=self.link_type_var, value="symlink").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(radio_frame, text="Duro (Hard Link)", variable=self.link_type_var, value="hard").pack(side=tk.LEFT, padx=5)
        
        if sys.platform == 'win32' and os.path.isdir(self.target_path):
            ttk.Radiobutton(radio_frame, text="Unión (Junction)", variable=self.link_type_var, value="junction").pack(side=tk.LEFT, padx=5)

        # Link Name
        tk.Label(grid_frame, text="Nombre del Enlace:", bg='#1e1e1e', fg='#ffffff').grid(row=2, column=0, sticky='w', pady=5)
        self.entry_name = ttk.Entry(grid_frame, width=40)
        self.entry_name.insert(0, self.target_path + "_link")
        self.entry_name.grid(row=2, column=1, pady=5, padx=10, sticky='w')

        # Buttons
        btn_frame = tk.Frame(self, bg='#1e1e1e')
        btn_frame.pack(pady=20, side=tk.BOTTOM, fill=tk.X)

        create_btn = ttk.Button(btn_frame, text="Crear", command=self.create)
        create_btn.pack(side=tk.RIGHT, padx=20)

        cancel_btn = ttk.Button(btn_frame, text="Cancelar", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=5)

    def create(self):
        ltype = self.link_type_var.get()
        link_name = self.entry_name.get().strip()
        
        if not link_name:
            messagebox.showerror("Error", "Debes especificar un nombre de enlace.")
            return

        try:
            FSManager.create_link(ltype, self.target_path, link_name)
            messagebox.showinfo("Éxito", f"Enlace '{ltype}' creado correctamente.")
            self.on_create()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error al crear enlace", f"Error:\n{e}")


class PyFSApp(tk.Tk):
    """
    Main PyFSManager GUI Application.
    """
    def __init__(self):
        super().__init__()
        self.title("PyFSManager - Manejador de Sistemas de Archivos")
        self.geometry("1100x700")
        self.minimum_size = (900, 600)
        self.configure(bg='#1e1e1e')
        
        self.current_dir = os.path.abspath(os.getcwd())
        self.selected_item: Optional[str] = None
        self.selected_meta: Optional[FileMetadata] = None

        self.setup_styles()
        self.setup_ui()
        self.load_directory(self.current_dir)

    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        # Configure Colors
        self.style.configure('.', background='#1e1e1e', foreground='#ffffff', font=('Segoe UI', 10))
        self.style.configure('TFrame', background='#1e1e1e')
        
        # Sidebar
        self.style.configure('Sidebar.TFrame', background='#252526')
        
        # Labels
        self.style.configure('TLabel', background='#1e1e1e', foreground='#ffffff')
        self.style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#007acc')
        self.style.configure('Header.TLabel', font=('Segoe UI', 10, 'bold'), foreground='#007acc')
        self.style.configure('Sidebar.TLabel', background='#252526', font=('Segoe UI', 10, 'bold'), foreground='#888888')
        
        # Treeview
        self.style.configure('Treeview', 
                             background='#2d2d2d', 
                             foreground='#ffffff', 
                             fieldbackground='#2d2d2d', 
                             rowheight=26,
                             font=('Segoe UI', 10),
                             borderwidth=0)
        self.style.map('Treeview', background=[('selected', '#007acc')])
        self.style.configure('Treeview.Heading', background='#3c3c3c', foreground='#ffffff', font=('Segoe UI', 10, 'bold'))

        # Buttons
        self.style.configure('TButton', background='#3c3c3c', foreground='#ffffff', borderwidth=0, font=('Segoe UI', 9))
        self.style.map('TButton', 
                       background=[('active', '#007acc'), ('disabled', '#252526')],
                       foreground=[('disabled', '#555555')])
        
        # Address Bar
        self.style.configure('Address.TEntry', fieldbackground='#2d2d2d', foreground='#ffffff', font=('Segoe UI', 10))

    def setup_ui(self):
        # --- Top Menu & Address Bar ---
        top_bar = tk.Frame(self, bg='#2d2d2d', height=50)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        # Back (Parent) Button
        btn_back = ttk.Button(top_bar, text="⬆ Atrás", width=8, command=self.go_to_parent)
        btn_back.pack(side=tk.LEFT, padx=10, pady=10)

        # Refresh Button
        btn_refresh = ttk.Button(top_bar, text="⟳ Recargar", width=10, command=self.refresh)
        btn_refresh.pack(side=tk.LEFT, padx=5, pady=10)

        # Path Entry
        self.path_var = tk.StringVar(value=self.current_dir)
        self.entry_path = ttk.Entry(top_bar, textvariable=self.path_var, font=('Segoe UI', 10))
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        self.entry_path.bind("<Return>", lambda e: self.go_to_path(self.path_var.get()))

        # Go Button
        btn_go = ttk.Button(top_bar, text="Ir ➔", width=6, command=lambda: self.go_to_path(self.path_var.get()))
        btn_go.pack(side=tk.LEFT, padx=10, pady=10)

        # --- Main Layout Splitter ---
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg='#3c3c3c', bd=0, sashwidth=4)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # 1. Left Sidebar (Bookmarks / Directory tree shortcuts)
        sidebar = tk.Frame(main_pane, bg='#252526', width=180)
        sidebar.pack(fill=tk.BOTH, expand=True)
        main_pane.add(sidebar)
        
        lbl_shortcuts = ttk.Label(sidebar, text="ACCESOS RÁPIDOS", style='Sidebar.TLabel')
        lbl_shortcuts.pack(anchor='w', padx=15, pady=(15, 5))

        shortcuts_frame = tk.Frame(sidebar, bg='#252526')
        shortcuts_frame.pack(fill=tk.X, padx=10)

        # Sidebar Shortcuts buttons
        def make_shortcut(name, path_getter):
            btn = tk.Button(
                shortcuts_frame, 
                text=name, 
                anchor='w', 
                bg='#252526', 
                fg='#ffffff',
                relief=tk.FLAT,
                bd=0,
                padx=10,
                pady=6,
                font=('Segoe UI', 10),
                activebackground='#007acc',
                activeforeground='#ffffff'
            )
            btn.configure(command=lambda: self.go_to_path(path_getter()))
            btn.pack(fill=tk.X, pady=2)
            
            # Hover effect
            btn.bind("<Enter>", lambda e: btn.configure(bg='#3c3c3c') if btn['bg'] != '#007acc' else None)
            btn.bind("<Leave>", lambda e: btn.configure(bg='#252526') if btn['bg'] != '#007acc' else None)

        make_shortcut("📁 Espacio Trabajo", lambda: os.getcwd())
        make_shortcut("🏠 Inicio (Home)", lambda: os.path.expanduser("~"))
        make_shortcut("🖥️ Escritorio", lambda: os.path.join(os.path.expanduser("~"), "Desktop"))
        make_shortcut("📄 Documentos", lambda: os.path.join(os.path.expanduser("~"), "Documents"))

        # 2. Center File list
        center_frame = tk.Frame(main_pane, bg='#1e1e1e')
        main_pane.add(center_frame)

        # File List Actions Header (Touch, Mkdir)
        actions_header = tk.Frame(center_frame, bg='#1e1e1e')
        actions_header.pack(fill=tk.X, padx=10, pady=5)
        
        btn_new_file = ttk.Button(actions_header, text="📄 Nuevo Archivo", command=self.action_touch)
        btn_new_file.pack(side=tk.LEFT, padx=5)

        btn_new_folder = ttk.Button(actions_header, text="📁 Nueva Carpeta", command=self.action_mkdir)
        btn_new_folder.pack(side=tk.LEFT, padx=5)

        # File Treeview
        tree_frame = tk.Frame(center_frame, bg='#1e1e1e')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ('name', 'type', 'size', 'mtime')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')
        
        self.tree.heading('name', text='Nombre', anchor='w')
        self.tree.heading('type', text='Tipo', anchor='w')
        self.tree.heading('size', text='Tamaño', anchor='e')
        self.tree.heading('mtime', text='Modificado', anchor='w')

        self.tree.column('name', width=250, anchor='w')
        self.tree.column('type', width=90, anchor='w')
        self.tree.column('size', width=95, anchor='e')
        self.tree.column('mtime', width=150, anchor='w')

        # Treeview scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.tree.bind("<Double-1>", self.on_item_double_click)

        # 3. Right Details & Actions Panel
        right_panel = tk.Frame(main_pane, bg='#252526', width=280)
        right_panel.pack(fill=tk.BOTH, expand=True)
        main_pane.add(right_panel)

        self.setup_right_panel(right_panel)

        # --- Bottom Status Console Log ---
        self.status_bar = tk.Text(self, bg='#111111', fg='#888888', height=4, font=('Consolas', 9), bd=0, padx=10, pady=5)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_status("Aplicación PyFSManager iniciada.")

    def setup_right_panel(self, parent):
        # Scrollable container for details panel in case screen is small
        canvas = tk.Canvas(parent, bg='#252526', bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg='#252526')

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw", width=280)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Section: Metadatos ---
        ttk.Label(scroll_frame, text="DETALLES", style='Header.TLabel').pack(anchor='w', padx=15, pady=(15, 5))
        
        self.lbl_name = ttk.Label(scroll_frame, text="Ningún elemento seleccionado", font=('Segoe UI', 10, 'bold'), wraplength=250, justify='left', background='#252526')
        self.lbl_name.pack(anchor='w', padx=15, pady=2)
        
        self.lbl_type = ttk.Label(scroll_frame, text="Tipo: -", background='#252526')
        self.lbl_type.pack(anchor='w', padx=15, pady=2)
        
        self.lbl_size = ttk.Label(scroll_frame, text="Tamaño: -", background='#252526')
        self.lbl_size.pack(anchor='w', padx=15, pady=2)
        
        self.lbl_link = ttk.Label(scroll_frame, text="", foreground='#007acc', background='#252526', wraplength=250, justify='left')
        self.lbl_link.pack(anchor='w', padx=15, pady=2)

        # --- Section: Tiempos ---
        ttk.Label(scroll_frame, text="MARCAS DE TIEMPO", style='Header.TLabel').pack(anchor='w', padx=15, pady=(15, 5))
        
        self.lbl_atime = ttk.Label(scroll_frame, text="Acceso: -", background='#252526')
        self.lbl_atime.pack(anchor='w', padx=15, pady=2)
        self.lbl_mtime = ttk.Label(scroll_frame, text="Modif: -", background='#252526')
        self.lbl_mtime.pack(anchor='w', padx=15, pady=2)
        self.lbl_ctime = ttk.Label(scroll_frame, text="Cambio: -", background='#252526')
        self.lbl_ctime.pack(anchor='w', padx=15, pady=2)
        self.lbl_birth = ttk.Label(scroll_frame, text="Creado: -", background='#252526')
        self.lbl_birth.pack(anchor='w', padx=15, pady=2)

        self.btn_edit_times = ttk.Button(scroll_frame, text="⏱ Editar Tiempos", command=self.action_edit_times, state=tk.DISABLED)
        self.btn_edit_times.pack(anchor='w', padx=15, pady=8)

        # --- Section: Permisos ---
        ttk.Label(scroll_frame, text="PERMISOS (POSIX/ACL)", style='Header.TLabel').pack(anchor='w', padx=15, pady=(10, 5))
        
        perms_frame = tk.Frame(scroll_frame, bg='#2d2d2d', padx=10, pady=10)
        perms_frame.pack(fill=tk.X, padx=15, pady=5)

        # Header Row
        tk.Label(perms_frame, text="Rol", font=('Segoe UI', 9, 'bold'), bg='#2d2d2d', fg='#888888').grid(row=0, column=0, sticky='w')
        tk.Label(perms_frame, text="R", font=('Segoe UI', 9, 'bold'), bg='#2d2d2d', fg='#888888').grid(row=0, column=1, padx=5)
        tk.Label(perms_frame, text="W", font=('Segoe UI', 9, 'bold'), bg='#2d2d2d', fg='#888888').grid(row=0, column=2, padx=5)
        tk.Label(perms_frame, text="X", font=('Segoe UI', 9, 'bold'), bg='#2d2d2d', fg='#888888').grid(row=0, column=3, padx=5)

        # Variables for checkboxes
        self.chk_vars = {
            'u': [tk.BooleanVar() for _ in range(3)],
            'g': [tk.BooleanVar() for _ in range(3)],
            'o': [tk.BooleanVar() for _ in range(3)]
        }

        # Checkboxes
        roles = [('Usuario (u)', 'u', 1), ('Grupo (g)', 'g', 2), ('Otros (o)', 'o', 3)]
        for label, key, row in roles:
            tk.Label(perms_frame, text=label, bg='#2d2d2d', fg='#ffffff', font=('Segoe UI', 9)).grid(row=row, column=0, sticky='w', pady=2)
            for i in range(3):
                chk = tk.Checkbutton(
                    perms_frame, 
                    variable=self.chk_vars[key][i], 
                    bg='#2d2d2d', 
                    activebackground='#2d2d2d', 
                    selectcolor='#1e1e1e',
                    bd=0
                )
                chk.grid(row=row, column=i+1, pady=2)

        self.btn_apply_perms = ttk.Button(scroll_frame, text="✓ Aplicar Permisos", command=self.action_apply_permissions, state=tk.DISABLED)
        self.btn_apply_perms.pack(anchor='w', padx=15, pady=5)

        # --- Section: Acciones ---
        ttk.Label(scroll_frame, text="ACCIONES", style='Header.TLabel').pack(anchor='w', padx=15, pady=(15, 5))
        
        actions_grid = tk.Frame(scroll_frame, bg='#252526')
        actions_grid.pack(fill=tk.X, padx=15, pady=5)

        self.btn_copy = ttk.Button(actions_grid, text="📄 Copiar", command=self.action_copy, state=tk.DISABLED)
        self.btn_copy.grid(row=0, column=0, padx=2, pady=4, sticky='ew')
        
        self.btn_move = ttk.Button(actions_grid, text="➔ Mover", command=self.action_move, state=tk.DISABLED)
        self.btn_move.grid(row=0, column=1, padx=2, pady=4, sticky='ew')

        self.btn_rename = ttk.Button(actions_grid, text="✏ Renombrar", command=self.action_rename, state=tk.DISABLED)
        self.btn_rename.grid(row=1, column=0, padx=2, pady=4, sticky='ew')
        
        self.btn_delete = ttk.Button(actions_grid, text="🗑 Eliminar", command=self.action_delete, state=tk.DISABLED)
        self.btn_delete.grid(row=1, column=1, padx=2, pady=4, sticky='ew')

        self.btn_link = ttk.Button(scroll_frame, text="🔗 Crear Enlace (Link)", command=self.action_create_link, state=tk.DISABLED)
        self.btn_link.pack(anchor='w', padx=15, pady=5, fill=tk.X)

        actions_grid.columnconfigure(0, weight=1)
        actions_grid.columnconfigure(1, weight=1)

    # --- UI Logic ---

    def log_status(self, msg: str, is_error: bool = False):
        t_str = time.strftime("%H:%M:%S")
        prefix = f"[{t_str}] [ERROR] " if is_error else f"[{t_str}] [OK] "
        
        self.status_bar.configure(state=tk.NORMAL)
        self.status_bar.insert(tk.END, prefix + msg + "\n")
        self.status_bar.see(tk.END)
        self.status_bar.configure(state=tk.DISABLED)

    def load_directory(self, path: str):
        path = os.path.abspath(path)
        try:
            # Check exist and is dir
            if not os.path.exists(path) or not os.path.isdir(path):
                messagebox.showerror("Error", f"La ruta no es un directorio válido: {path}")
                return

            self.current_dir = path
            self.path_var.set(self.current_dir)
            
            # Clear treeview
            for child in self.tree.get_children():
                self.tree.delete(child)

            # Read items
            items = os.listdir(self.current_dir)
            
            # Retrieve metadata
            item_metas = []
            for item in items:
                p = os.path.join(self.current_dir, item)
                try:
                    meta = FSManager.get_metadata(p)
                    item_metas.append(meta)
                except Exception:
                    pass

            # Sort items: directory, junction, symlink, others... then alphabetically
            def sort_key(meta: FileMetadata):
                type_order = {'directory': 0, 'junction': 1, 'symlink': 2, 'fifo': 3, 'socket': 4, 'regular': 5, 'unknown': 6}
                return (type_order.get(meta.type, 9), meta.name.lower())

            item_metas.sort(key=sort_key)

            # Insert to Treeview
            for meta in item_metas:
                # Icon prefix
                prefix = ""
                if meta.type == 'directory': prefix = "📁 "
                elif meta.type in ('symlink', 'junction'): prefix = "🔗 "
                elif 'x' in meta.permissions.user and meta.type == 'regular': prefix = "⚙️ "
                else: prefix = "📄 "

                display_name = prefix + meta.name
                size_str = format_size(meta.size) if meta.type == 'regular' else '-'
                mtime_str = format_time(meta.mtime)
                
                self.tree.insert(
                    '', 
                    tk.END, 
                    iid=meta.path, 
                    values=(display_name, meta.type.upper(), size_str, mtime_str)
                )

            self.clear_selection()
            self.log_status(f"Directorio cargado: {self.current_dir}")
        except Exception as e:
            self.log_status(f"Error al cargar directorio: {e}", is_error=True)
            messagebox.showerror("Error", f"No se pudo cargar el directorio:\n{e}")

    def clear_selection(self):
        self.selected_item = None
        self.selected_meta = None
        
        self.lbl_name.configure(text="Ningún elemento seleccionado", foreground='#ffffff')
        self.lbl_type.configure(text="Tipo: -")
        self.lbl_size.configure(text="Tamaño: -")
        self.lbl_link.configure(text="")
        
        self.lbl_atime.configure(text="Acceso: -")
        self.lbl_mtime.configure(text="Modif: -")
        self.lbl_ctime.configure(text="Cambio: -")
        self.lbl_birth.configure(text="Creado: -")

        # Disable checkboxes & buttons
        for key in self.chk_vars:
            for var in self.chk_vars[key]:
                var.set(False)

        self.btn_edit_times.configure(state=tk.DISABLED)
        self.btn_apply_perms.configure(state=tk.DISABLED)
        self.btn_copy.configure(state=tk.DISABLED)
        self.btn_move.configure(state=tk.DISABLED)
        self.btn_rename.configure(state=tk.DISABLED)
        self.btn_delete.configure(state=tk.DISABLED)
        self.btn_link.configure(state=tk.DISABLED)

    def on_item_select(self, event):
        selection = self.tree.selection()
        if not selection:
            self.clear_selection()
            return

        filepath = selection[0]
        self.selected_item = filepath

        try:
            self.selected_meta = FSManager.get_metadata(filepath)
            meta = self.selected_meta
            
            # Update labels
            self.lbl_name.configure(text=meta.name, foreground='#007acc')
            self.lbl_type.configure(text=f"Tipo: {meta.type.upper()}")
            self.lbl_size.configure(text=f"Tamaño: {meta.size} bytes ({format_size(meta.size)})")
            
            if meta.link_target:
                self.lbl_link.configure(text=f"Destino: {meta.link_target}")
            else:
                self.lbl_link.configure(text="")

            self.lbl_atime.configure(text=f"Acceso: {format_time(meta.atime)}")
            self.lbl_mtime.configure(text=f"Modif: {format_time(meta.mtime)}")
            self.lbl_ctime.configure(text=f"Cambio: {format_time(meta.ctime)}")
            
            if meta.birthtime:
                self.lbl_birth.configure(text=f"Creado: {format_time(meta.birthtime)}")
            else:
                self.lbl_birth.configure(text="Creado: N/D")

            # Enable/Update permissions checkboxes
            perms = meta.permissions
            
            def set_chk(vars_list, rwx_str):
                vars_list[0].set('r' in rwx_str)
                vars_list[1].set('w' in rwx_str)
                vars_list[2].set('x' in rwx_str)

            set_chk(self.chk_vars['u'], perms.user)
            set_chk(self.chk_vars['g'], perms.group)
            set_chk(self.chk_vars['o'], perms.other)

            # Enable buttons
            self.btn_edit_times.configure(state=tk.NORMAL)
            self.btn_apply_perms.configure(state=tk.NORMAL)
            self.btn_copy.configure(state=tk.NORMAL)
            self.btn_move.configure(state=tk.NORMAL)
            self.btn_rename.configure(state=tk.NORMAL)
            self.btn_delete.configure(state=tk.NORMAL)
            self.btn_link.configure(state=tk.NORMAL)
        except Exception as e:
            self.log_status(f"Error al leer metadatos de '{filepath}': {e}", is_error=True)

    def on_item_double_click(self, event):
        if not self.selected_item:
            return

        meta = self.selected_meta
        if not meta:
            return

        if meta.type == 'directory' or meta.type == 'junction':
            self.go_to_path(self.selected_item)
        elif meta.type == 'symlink':
            # Check if target is directory
            if os.path.isdir(self.selected_item):
                self.go_to_path(self.selected_item)
            else:
                self.action_edit_file()
        elif meta.type == 'regular':
            self.action_edit_file()

    def go_to_parent(self):
        parent = os.path.dirname(self.current_dir)
        # Check if parent is same (e.g. root C:\ or /)
        if parent == self.current_dir:
            return
        self.go_to_path(parent)

    def go_to_path(self, path: str):
        path = os.path.abspath(path)
        self.load_directory(path)

    def refresh(self):
        self.load_directory(self.current_dir)

    # --- Actions ---

    def action_touch(self):
        filename = filedialog.asksaveasfilename(
            initialdir=self.current_dir,
            title="Crear Nuevo Archivo",
            confirmoverwrite=True
        )
        if filename:
            try:
                FSManager.touch(filename)
                self.log_status(f"Archivo creado: {filename}")
                self.refresh()
            except Exception as e:
                self.log_status(f"Error al crear archivo: {e}", is_error=True)
                messagebox.showerror("Error", f"No se pudo crear el archivo:\n{e}")

    def action_mkdir(self):
        from tkinter import simpledialog
        foldername = simpledialog.askstring("Nueva Carpeta", "Introduce el nombre de la carpeta:")
        if foldername:
            path = os.path.join(self.current_dir, foldername)
            try:
                FSManager.mkdir(path)
                self.log_status(f"Directorio creado: {path}")
                self.refresh()
            except Exception as e:
                self.log_status(f"Error al crear directorio: {e}", is_error=True)
                messagebox.showerror("Error", f"No se pudo crear la carpeta:\n{e}")

    def action_edit_file(self):
        if not self.selected_item:
            return
        editor = FileEditorWindow(self, self.selected_item)
        # Center dialog
        editor.geometry("+%d+%d" % (self.winfo_x() + 100, self.winfo_y() + 50))

    def action_edit_times(self):
        if not self.selected_item or not self.selected_meta:
            return
        dialog = EditTimesDialog(self, self.selected_item, self.selected_meta, self.refresh)
        dialog.geometry("+%d+%d" % (self.winfo_x() + 200, self.winfo_y() + 150))

    def action_apply_permissions(self):
        if not self.selected_item:
            return
            
        # Build rwx strings
        def get_rwx_str(vars_list):
            r = 'r' if vars_list[0].get() else '-'
            w = 'w' if vars_list[1].get() else '-'
            x = 'x' if vars_list[2].get() else '-'
            return r + w + x

        u_str = get_rwx_str(self.chk_vars['u'])
        g_str = get_rwx_str(self.chk_vars['g'])
        o_str = get_rwx_str(self.chk_vars['o'])
        
        perms = FilePermissions(u_str, g_str, o_str)

        try:
            FSManager.set_permissions(self.selected_item, perms)
            self.log_status(f"Permisos aplicados a '{self.selected_item}': {perms.to_symbolic()}")
            self.refresh()
            # Select item again to reload display
            self.tree.selection_set(self.selected_item)
        except Exception as e:
            self.log_status(f"Error al aplicar permisos: {e}", is_error=True)
            messagebox.showerror("Error", f"No se pudieron cambiar los permisos:\n{e}")

    def action_copy(self):
        if not self.selected_item:
            return
        dst = filedialog.asksaveasfilename(
            initialdir=self.current_dir,
            title="Copiar elemento a...",
            initialfile=os.path.basename(self.selected_item)
        )
        if dst:
            try:
                FSManager.copy(self.selected_item, dst)
                self.log_status(f"Elemento copiado de '{self.selected_item}' a '{dst}'")
                self.refresh()
            except Exception as e:
                self.log_status(f"Error al copiar: {e}", is_error=True)
                messagebox.showerror("Error al copiar", f"No se pudo copiar:\n{e}")

    def action_move(self):
        if not self.selected_item:
            return
        dst = filedialog.asksaveasfilename(
            initialdir=self.current_dir,
            title="Mover elemento a...",
            initialfile=os.path.basename(self.selected_item)
        )
        if dst:
            try:
                FSManager.move(self.selected_item, dst)
                self.log_status(f"Elemento movido de '{self.selected_item}' a '{dst}'")
                self.refresh()
            except Exception as e:
                self.log_status(f"Error al mover: {e}", is_error=True)
                messagebox.showerror("Error al mover", f"No se pudo mover:\n{e}")

    def action_rename(self):
        if not self.selected_item:
            return
        from tkinter import simpledialog
        old_name = os.path.basename(self.selected_item)
        new_name = simpledialog.askstring("Renombrar", f"Modifica el nombre para '{old_name}':", initialvalue=old_name)
        if new_name and new_name != old_name:
            dst = os.path.join(os.path.dirname(self.selected_item), new_name)
            try:
                FSManager.move(self.selected_item, dst)
                self.log_status(f"Renombrado de '{old_name}' a '{new_name}'")
                self.refresh()
            except Exception as e:
                self.log_status(f"Error al renombrar: {e}", is_error=True)
                messagebox.showerror("Error", f"No se pudo renombrar:\n{e}")

    def action_delete(self):
        if not self.selected_item:
            return
        name = os.path.basename(self.selected_item)
        confirm = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Estás seguro de que deseas eliminar permanentemente '{name}'?\nEsta operación no se puede deshacer."
        )
        if confirm:
            try:
                FSManager.delete(self.selected_item)
                self.log_status(f"Eliminado: {self.selected_item}")
                self.refresh()
            except Exception as e:
                self.log_status(f"Error al eliminar: {e}", is_error=True)
                messagebox.showerror("Error", f"No se pudo eliminar:\n{e}")

    def action_create_link(self):
        if not self.selected_item:
            return
        dialog = CreateLinkDialog(self, self.selected_item, self.refresh)
        dialog.geometry("+%d+%d" % (self.winfo_x() + 200, self.winfo_y() + 150))


def main():
    app = PyFSApp()
    app.mainloop()

if __name__ == '__main__':
    main()
