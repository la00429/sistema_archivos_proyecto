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

# Theme colors (centralized for easier tweaks)
THEME_BG = '#0f1218'
PANEL_BG = '#151a22'
PANEL_ALT = '#1b2230'
SURFACE = '#1f2633'
ACCENT = '#5b8cff'
ACCENT_HOVER = '#7aa2ff'
ON_ACCENT = '#ffffff'
MUTED = '#8b97a7'
TEXT_PRIMARY = '#ecf2ff'
TEXT_SECONDARY = '#c4cfde'
HEADER_BG = '#171d27'
STATUS_BG = '#0c1016'
STATUS_FG = '#d5deea'
DISABLED_FG = '#5b6676'
BORDER_BG = '#2b3443'
INPUT_BG = '#111722'
CARD_BG = '#171e29'
CARD_ELEVATED = '#1c2431'

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


def apply_modern_palette(widget):
    widget.configure(bg=THEME_BG)
    style = ttk.Style(widget)
    try:
        style.theme_use('clam')
    except tk.TclError:
        pass

    style.configure('.', background=THEME_BG, foreground=TEXT_PRIMARY)
    style.configure('TFrame', background=THEME_BG)
    style.configure('Surface.TFrame', background=PANEL_BG)
    style.configure('Card.TFrame', background=CARD_BG)
    style.configure('Header.TFrame', background=HEADER_BG)
    style.configure('TLabel', background=THEME_BG, foreground=TEXT_PRIMARY)
    style.configure('Muted.TLabel', background=THEME_BG, foreground=MUTED)
    style.configure('Title.TLabel', background=THEME_BG, foreground=TEXT_PRIMARY, font=('Segoe UI Semibold', 16))
    style.configure('Subtitle.TLabel', background=THEME_BG, foreground=TEXT_SECONDARY, font=('Segoe UI', 9))
    style.configure('Section.TLabel', background=CARD_BG, foreground=ACCENT, font=('Segoe UI Semibold', 10))
    style.configure('CardTitle.TLabel', background=CARD_BG, foreground=TEXT_PRIMARY, font=('Segoe UI Semibold', 14))
    style.configure('CardSubtitle.TLabel', background=CARD_BG, foreground=TEXT_SECONDARY, font=('Segoe UI', 9))
    style.configure('CardValue.TLabel', background=CARD_BG, foreground=TEXT_PRIMARY, font=('Segoe UI', 10))
    style.configure('TButton', padding=(12, 7), borderwidth=0, focusthickness=1, focuscolor=ACCENT)
    style.map(
        'TButton',
        foreground=[('disabled', DISABLED_FG), ('pressed', ON_ACCENT), ('active', ON_ACCENT)],
        background=[('disabled', BORDER_BG), ('pressed', ACCENT_HOVER), ('active', ACCENT_HOVER)],
        relief=[('pressed', 'flat'), ('!pressed', 'flat')],
    )
    style.configure('Accent.TButton', background=ACCENT, foreground=ON_ACCENT)
    style.map('Accent.TButton', background=[('active', ACCENT_HOVER), ('pressed', ACCENT_HOVER)])
    style.configure(
        'TEntry',
        fieldbackground=INPUT_BG,
        background=INPUT_BG,
        foreground=TEXT_PRIMARY,
        bordercolor=BORDER_BG,
        lightcolor=BORDER_BG,
        darkcolor=BORDER_BG,
        insertcolor=TEXT_PRIMARY,
        padding=8,
        relief='flat',
    )
    style.configure('Treeview', background=CARD_BG, fieldbackground=CARD_BG, foreground=TEXT_PRIMARY, rowheight=30, borderwidth=0)
    style.configure('Treeview.Heading', background=PANEL_BG, foreground=TEXT_PRIMARY, relief='flat', padding=(10, 8))
    style.map('Treeview', background=[('selected', ACCENT)], foreground=[('selected', ON_ACCENT)])
    style.map('Treeview.Heading', background=[('active', PANEL_ALT)])
    style.configure('TScrollbar', background=PANEL_BG, troughcolor=THEME_BG, arrowcolor=TEXT_PRIMARY, bordercolor=THEME_BG)


def style_modern_entry(entry, *, readonly: bool = False):
    entry.configure(
        bg=INPUT_BG,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        relief='flat',
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER_BG,
        highlightcolor=ACCENT,
        selectbackground=ACCENT,
        selectforeground=ON_ACCENT,
        disabledbackground=INPUT_BG,
        disabledforeground=MUTED,
    )
    if readonly:
        entry.configure(readonlybackground=INPUT_BG, state='readonly')


def style_modern_text(widget, *, readonly: bool = False, wrap=tk.WORD):
    widget.configure(
        bg=INPUT_BG,
        fg=TEXT_PRIMARY,
        insertbackground=TEXT_PRIMARY,
        selectbackground=ACCENT,
        selectforeground=ON_ACCENT,
        relief='flat',
        bd=0,
        highlightthickness=1,
        highlightbackground=BORDER_BG,
        highlightcolor=ACCENT,
        padx=12,
        pady=12,
        wrap=wrap,
    )
    if readonly:
        widget.configure(state=tk.DISABLED)


def bind_windows_text_shortcuts(widget, *, allow_cut: bool = True, allow_paste: bool = True, allow_undo: bool = True):
    def select_all(event=None):
        try:
            widget.tag_add(tk.SEL, '1.0', tk.END)
            widget.mark_set(tk.INSERT, tk.END)
            widget.see(tk.INSERT)
        except tk.TclError:
            pass
        return 'break'

    def copy_selection(event=None):
        try:
            text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            widget.clipboard_clear()
            widget.clipboard_append(text)
        except tk.TclError:
            pass
        return 'break'

    def cut_selection(event=None):
        if not allow_cut:
            return 'break'
        try:
            text = widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            widget.clipboard_clear()
            widget.clipboard_append(text)
            widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            pass
        return 'break'

    def paste_clipboard(event=None):
        if not allow_paste:
            return 'break'
        try:
            widget.insert(tk.INSERT, widget.clipboard_get())
        except tk.TclError:
            pass
        return 'break'

    def undo_action(event=None):
        if not allow_undo:
            return 'break'
        try:
            widget.edit_undo()
        except tk.TclError:
            pass
        return 'break'

    def redo_action(event=None):
        if not allow_undo:
            return 'break'
        try:
            widget.edit_redo()
        except tk.TclError:
            pass
        return 'break'

    widget.bind('<Control-a>', select_all)
    widget.bind('<Control-A>', select_all)
    widget.bind('<Control-c>', copy_selection)
    widget.bind('<Control-C>', copy_selection)
    widget.bind('<Control-x>', cut_selection)
    widget.bind('<Control-X>', cut_selection)
    widget.bind('<Control-v>', paste_clipboard)
    widget.bind('<Control-V>', paste_clipboard)
    widget.bind('<Control-z>', undo_action)
    widget.bind('<Control-Z>', undo_action)
    widget.bind('<Control-y>', redo_action)
    widget.bind('<Control-Y>', redo_action)
    widget.bind('<Control-Shift-Z>', redo_action)
    return widget


def style_modern_menu(menu):
    menu.configure(
        bg=PANEL_BG,
        fg=TEXT_PRIMARY,
        activebackground=ACCENT,
        activeforeground=ON_ACCENT,
        bd=0,
        relief='flat',
        tearoff=0,
    )

class FileEditorWindow(tk.Toplevel):
    """
    Built-in Text Editor / Hex Viewer dialog.
    Automatically detects file type (text vs binary) and presents an editor or viewer.
    """
    def __init__(self, parent, filepath: str, view_mode: str = 'auto'):
        super().__init__(parent)
        apply_modern_palette(self)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.filepath = os.path.abspath(filepath)
        self.filename = os.path.basename(filepath)
        self.view_mode = view_mode
        self.title(f"Editor - {self.filename}")
        self.geometry("800x600")
        self.minsize(720, 520)
        
        
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
        main_frame = ttk.Frame(self, padding=16, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        header_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=(16, 14))
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, 12))

        type_lbl = ttk.Label(header_frame, text=f"Archivo: {self.filename}", style='CardTitle.TLabel')
        type_lbl.pack(anchor='w')

        meta_lbl = ttk.Label(
            header_frame,
            text=f"Tipo: {self.file_type.upper()} · Codificación: {self.encoding.upper()}",
            style='CardSubtitle.TLabel',
        )
        meta_lbl.pack(anchor='w', pady=(4, 0))

        content_frame = ttk.Frame(main_frame, style='Card.TFrame')
        content_frame.grid(row=1, column=0, sticky='nsew')
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        display_mode = self.file_type if self.view_mode == 'auto' else self.view_mode

        # Content Text Area
        self.txt_area = tk.Text(
            content_frame,
            font=('Consolas', 11),
            wrap=tk.WORD if display_mode in ('text', 'pdf') else tk.NONE,
            padx=12,
            pady=12,
            bd=0,
            relief='flat',
            undo=True,
            autoseparators=True,
            maxundo=500,
            exportselection=False,
        )
        style_modern_text(self.txt_area, wrap=tk.WORD if display_mode in ('text', 'pdf') else tk.NONE)
        bind_windows_text_shortcuts(self.txt_area, allow_cut=(display_mode == 'text'), allow_paste=(display_mode == 'text'), allow_undo=(display_mode == 'text'))

        # Scrollbar
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=self.txt_area.yview)
        self.txt_area.configure(yscrollcommand=scrollbar.set)

        self.txt_area.grid(row=0, column=0, sticky='nsew')
        scrollbar.grid(row=0, column=1, sticky='ns')

        # Load content
        if display_mode == 'pdf':
            try:
                from pypdf import PdfReader
                reader = PdfReader(self.filepath)
                pages = []
                for page in reader.pages[:3]:
                    pages.append(page.extract_text() or "(sin texto extraíble en esta página)")
                self.txt_area.insert(tk.END, f"Documento PDF\nPáginas: {len(reader.pages)}\n\n" + "\n\n--- Página ---\n\n".join(pages))
            except Exception as e:
                self.txt_area.insert(tk.END, f"No se pudo renderizar el PDF en esta vista.\n\n{e}")
            self.txt_area.configure(state=tk.DISABLED)

            btn_frame = ttk.Frame(main_frame, style='TFrame')
            btn_frame.grid(row=2, column=0, sticky='ew', pady=(12, 0))
            close_btn = ttk.Button(btn_frame, text="Cerrar", command=self.destroy, style='Accent.TButton')
            close_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        elif display_mode == 'binary':
            # View-only Hexdump
            from .cli import hex_dump
            self.txt_area.insert(tk.END, hex_dump(self.content))
            self.txt_area.configure(state=tk.DISABLED)
            
            # Bottom action bar (close only)
            btn_frame = ttk.Frame(main_frame, style='TFrame')
            btn_frame.grid(row=2, column=0, sticky='ew', pady=(12, 0))
            close_btn = ttk.Button(btn_frame, text="Cerrar", command=self.destroy, style='Accent.TButton')
            close_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        else:
            # Edit text mode
            if isinstance(self.content, bytes):
                self.txt_area.insert(tk.END, self.content.decode(self.encoding, errors='replace'))
            else:
                self.txt_area.insert(tk.END, self.content)
            self.txt_area.edit_reset()
            self.txt_area.focus_set()
            self.bind('<Control-s>', lambda e: self.save_file())
            
            # Bottom action bar (Save/Cancel)
            btn_frame = ttk.Frame(main_frame, style='TFrame')
            btn_frame.grid(row=2, column=0, sticky='ew', pady=(12, 0))
            
            save_btn = ttk.Button(btn_frame, text="Guardar", command=self.save_file, style='Accent.TButton')
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
        apply_modern_palette(self)
        self.filepath = filepath
        self.meta = meta
        self.on_save = on_save_callback
        
        self.title("Modificar Marcas de Tiempo")
        self.geometry("450x250")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

    def format_ts(self, ts) -> str:
        if not ts:
            return ""
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

    def parse_time_str(self, time_str: str) -> Optional[float]:
        time_str = time_str.strip
        if not time_str:
            return None
        try:
            struct = time.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            return time.mktime(struct)
        except ValueError:
            raise ValueError(f"Formato incorrecto para '{time_str}'. Usar YYYY-MM-DD HH:MM:SS")

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=16, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main_frame, style='Card.TFrame', padding=(16, 12))
        header.pack(fill=tk.X, pady=(0, 12))

        lbl = ttk.Label(header, text="Editar marcas de tiempo", style='CardTitle.TLabel')
        lbl.pack(anchor='w')

        ttk.Label(header, text="Edita atime, mtime y birthtime con un formato consistente.", style='CardSubtitle.TLabel').pack(anchor='w', pady=(4, 0))

        grid_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=16)
        grid_frame.pack(fill=tk.X)

        # Atime
        ttk.Label(grid_frame, text="Acceso (atime):").grid(row=0, column=0, sticky='w', pady=5)
        self.entry_atime = tk.Entry(grid_frame, width=30)
        self.entry_atime.insert(0, self.format_ts(self.meta.atime))
        self.entry_atime.grid(row=0, column=1, pady=5, padx=10)
        style_modern_entry(self.entry_atime)

        # Mtime
        ttk.Label(grid_frame, text="Modificación (mtime):").grid(row=1, column=0, sticky='w', pady=5)
        self.entry_mtime = tk.Entry(grid_frame, width=30)
        self.entry_mtime.insert(0, self.format_ts(self.meta.mtime))
        self.entry_mtime.grid(row=1, column=1, pady=5, padx=10)
        style_modern_entry(self.entry_mtime)

        # Birthtime (Only editable on Windows)
        ttk.Label(grid_frame, text="Creación (birthtime):").grid(row=2, column=0, sticky='w', pady=5)
        self.entry_birth = tk.Entry(grid_frame, width=30)
        if self.meta.birthtime:
            self.entry_birth.insert(0, self.format_ts(self.meta.birthtime))
        else:
            self.entry_birth.insert(0, "No soportado en este S.O.")
            self.entry_birth.configure(state=tk.DISABLED)
        self.entry_birth.grid(row=2, column=1, pady=5, padx=10)
        style_modern_entry(self.entry_birth)

        # Buttons
        btn_frame = ttk.Frame(main_frame, style='TFrame')
        btn_frame.pack(pady=(14, 0), side=tk.BOTTOM, fill=tk.X)

        save_btn = ttk.Button(btn_frame, text="Guardar", command=self.save, style='Accent.TButton')
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
        apply_modern_palette(self)
        self.target_path = os.path.abspath(target_path)
        self.on_create = on_create_callback
        
        self.title("Crear Enlace / Link")
        self.geometry("500x230")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=16, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main_frame, style='Card.TFrame', padding=(16, 12))
        header.pack(fill=tk.X, pady=(0, 12))

        lbl = ttk.Label(header, text="Crear nuevo enlace", style='CardTitle.TLabel')
        lbl.pack(anchor='w')

        ttk.Label(header, text="Elige el tipo de enlace y define su nombre.", style='CardSubtitle.TLabel').pack(anchor='w', pady=(4, 0))

        grid_frame = ttk.Frame(main_frame, style='Card.TFrame', padding=16)
        grid_frame.pack(fill=tk.X)

        # Target (readonly)
        ttk.Label(grid_frame, text="Destino (Target):").grid(row=0, column=0, sticky='w', pady=5)
        lbl_target = ttk.Label(grid_frame, text=self.target_path, anchor='w', justify='left')
        lbl_target.grid(row=0, column=1, pady=5, padx=10, sticky='w')

        # Link Type
        ttk.Label(grid_frame, text="Tipo de Enlace:").grid(row=1, column=0, sticky='w', pady=5)
        self.link_type_var = tk.StringVar(value="symlink")
        
        radio_frame = ttk.Frame(grid_frame)
        radio_frame.grid(row=1, column=1, pady=5, padx=10, sticky='w')
        
        ttk.Radiobutton(radio_frame, text="Simbólico (Symlink)", variable=self.link_type_var, value="symlink").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(radio_frame, text="Duro (Hard Link)", variable=self.link_type_var, value="hard").pack(side=tk.LEFT, padx=5)
        
        if sys.platform == 'win32' and os.path.isdir(self.target_path):
            ttk.Radiobutton(radio_frame, text="Unión (Junction)", variable=self.link_type_var, value="junction").pack(side=tk.LEFT, padx=5)

        # Link Name
        ttk.Label(grid_frame, text="Nombre del Enlace:").grid(row=2, column=0, sticky='w', pady=5)
        self.entry_name = tk.Entry(grid_frame, width=40)
        self.entry_name.insert(0, self.target_path + "_link")
        self.entry_name.grid(row=2, column=1, pady=5, padx=10, sticky='w')
        style_modern_entry(self.entry_name)

        # Buttons
        btn_frame = ttk.Frame(main_frame, style='TFrame')
        btn_frame.pack(pady=(14, 0), side=tk.BOTTOM, fill=tk.X)

        create_btn = ttk.Button(btn_frame, text="Crear", command=self.create, style='Accent.TButton')
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



class CustomFileDialog(tk.Toplevel):
    """
    React-like custom file dialog replacing OS native dialogs.
    """
    def __init__(self, parent, initialdir, title="Seleccionar", mode='saveas', initialfile=""):
        super().__init__(parent)
        apply_modern_palette(self)
        self.title(title)
        self.geometry("650x450")
        self.transient(parent)
        self.grab_set()

        self.current_dir = os.path.abspath(initialdir)
        self.mode = mode
        self.result = None
        
        self.configure(bg=PANEL_BG)
        self.setup_ui()
        self.load_directory(self.current_dir)
        
        if mode == 'saveas' and initialfile:
            self.entry_name.insert(0, initialfile)

        self.wait_window(self)

    def setup_ui(self):
        # Estilo React-like: Paddings amplios, fondos limpios
        main_frame = ttk.Frame(self, padding=15, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        top_bar = ttk.Frame(main_frame, style='Card.TFrame', padding=12)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        btn_back = ttk.Button(top_bar, text="⬅ Atrás", command=self.go_up)
        btn_back.pack(side=tk.LEFT, padx=(0, 10))
        
        self.path_var = tk.StringVar(value=self.current_dir)
        path_entry = tk.Entry(top_bar, textvariable=self.path_var, font=('Segoe UI', 10))
        style_modern_entry(path_entry, readonly=True)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Treeview content
        tree_frame = ttk.Frame(main_frame, style='Card.TFrame')
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_frame, columns=('name', 'type'), show='headings', selectmode='browse')
        self.tree.heading('name', text='Nombre', anchor='w')
        self.tree.heading('type', text='Tipo', anchor='w')
        self.tree.column('name', width=450, anchor='w')
        self.tree.column('type', width=120, anchor='w')
        
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        # Bottom bar
        bottom_bar = ttk.Frame(main_frame, style='TFrame')
        bottom_bar.pack(fill=tk.X, pady=(15, 0))
        
        if self.mode == 'saveas':
            ttk.Label(bottom_bar, text="Nombre del archivo:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
            self.entry_name = tk.Entry(bottom_bar, font=('Segoe UI', 10))
            style_modern_entry(self.entry_name)
            self.entry_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
            ttk.Button(bottom_bar, text="Guardar", command=self.confirm, style='Accent.TButton').pack(side=tk.RIGHT)
        else:
            ttk.Label(bottom_bar, text="Carpeta seleccionada:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 10))
            self.entry_name = tk.Entry(bottom_bar, font=('Segoe UI', 10))
            style_modern_entry(self.entry_name)
            self.entry_name.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
            ttk.Button(bottom_bar, text="Seleccionar Carpeta", command=self.confirm, style='Accent.TButton').pack(side=tk.RIGHT)
            
        ttk.Button(bottom_bar, text="Cancelar", command=self.destroy).pack(side=tk.RIGHT, padx=10)

    def load_directory(self, path):
        try:
            self.current_dir = os.path.abspath(path)
            self.path_var.set(self.current_dir)
            if self.mode == 'directory':
                self.entry_name.delete(0, tk.END)
                self.entry_name.insert(0, os.path.basename(self.current_dir))
                
            for item in self.tree.get_children():
                self.tree.delete(item)
                
            items = os.listdir(self.current_dir)
            dirs = []
            files = []
            for name in items:
                full_path = os.path.join(self.current_dir, name)
                if os.path.isdir(full_path):
                    dirs.append((name, full_path))
                else:
                    files.append((name, full_path))
            
            for name, full_path in sorted(dirs):
                self.tree.insert('', tk.END, iid=full_path, values=("📁 " + name, "Carpeta"))
            for name, full_path in sorted(files):
                self.tree.insert('', tk.END, iid=full_path, values=("📄 " + name, "Archivo"))
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo acceder a la carpeta:\n{e}")
            self.go_up()

    def go_up(self):
        parent = os.path.dirname(self.current_dir)
        if parent != self.current_dir:
            self.load_directory(parent)

    def on_double_click(self, event):
        selection = self.tree.selection()
        if not selection: return
        path = selection[0]
        if os.path.isdir(path):
            self.load_directory(path)

    def on_select(self, event):
        if self.mode == 'saveas':
            selection = self.tree.selection()
            if selection:
                path = selection[0]
                if os.path.isfile(path):
                    self.entry_name.delete(0, tk.END)
                    self.entry_name.insert(0, os.path.basename(path))

    def confirm(self):
        if self.mode == 'saveas':
            filename = self.entry_name.get().strip()
            if not filename:
                messagebox.showerror("Error", "Debes ingresar un nombre de archivo.")
                return
            self.result = os.path.join(self.current_dir, filename)
        else:
            self.result = self.current_dir
        self.destroy()

class PyFSApp(tk.Tk):
    """
    Main PyFSManager GUI Application.
    """
    def __init__(self):
        super().__init__()
        apply_modern_palette(self)
        self.title("PyFSManager - Manejador de Sistemas de Archivos")
        self.geometry("1100x700")
        self.minsize(900, 600)  # Bug 6 fix: use minsize to actually enforce the minimum window size
        
        # Link FSManager log callback to our log_status
        FSManager.set_log_callback(self.log_status)
        
        self.current_dir = os.path.abspath(os.getcwd())
        self.selected_item: Optional[str] = None
        self.selected_meta: Optional[FileMetadata] = None

        self.setup_styles()
        self.setup_ui()
        self.load_directory(self.current_dir)

    def setup_styles(self):
        # All styling is centralized in apply_modern_palette(self).
        return

    def setup_ui(self):
        self.root_frame = ttk.Frame(self, style='TFrame')
        self.root_frame.pack(fill=tk.BOTH, expand=True)
        # --- Top Banner ---
        top_banner = ttk.Frame(self.root_frame, style='Card.TFrame', padding=(16, 14))
        top_banner.pack(side=tk.TOP, fill=tk.X, padx=16, pady=(16, 10))

        title_row = ttk.Frame(top_banner, style='Card.TFrame')
        title_row.pack(fill=tk.X)

        title_block = ttk.Frame(title_row, style='Card.TFrame')
        title_block.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(title_block, text="PyFSManager", style='Title.TLabel').pack(anchor='w')
        ttk.Label(
            title_block,
            text="Explorador visual con permisos, metadatos y enlaces en una sola vista.",
            style='Subtitle.TLabel'
        ).pack(anchor='w', pady=(4, 0))

        self.path_chip = ttk.Label(title_row, text=self.current_dir, style='Subtitle.TLabel', anchor='e', justify='right')
        self.path_chip.pack(side=tk.RIGHT)

        # --- Top Menu & Address Bar ---
        top_bar = ttk.Frame(self.root_frame, style='Card.TFrame', padding=(12, 12))
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=16, pady=(0, 12))

        # Back (Parent) Button
        btn_back = ttk.Button(top_bar, text="⬆ Atrás", width=8, command=self.go_to_parent)
        btn_back.pack(side=tk.LEFT, padx=10, pady=10)

        # Refresh Button
        btn_refresh = ttk.Button(top_bar, text="⟳ Recargar", width=10, command=self.refresh)
        btn_refresh.pack(side=tk.LEFT, padx=5, pady=10)

        # Path Entry
        self.path_var = tk.StringVar(value=self.current_dir)
        self.entry_path = tk.Entry(top_bar, textvariable=self.path_var, font=('Segoe UI', 10))
        style_modern_entry(self.entry_path)
        self.entry_path.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
        self.entry_path.bind("<Return>", lambda e: self.go_to_path(self.path_var.get()))

        # Search / Filter Entry
        self.filter_var = tk.StringVar(value='')
        self.entry_search = tk.Entry(top_bar, textvariable=self.filter_var, width=30)
        style_modern_entry(self.entry_search)
        self.entry_search.pack(side=tk.RIGHT, padx=10, pady=10)
        # Mejora 4: Placeholder text for search bar
        self._search_placeholder = '\U0001f50d Filtrar...'  # magnifying glass
        self.entry_search.insert(0, self._search_placeholder)
        self.entry_search.configure(fg=MUTED)
        self.entry_search.bind('<FocusIn>', self._on_search_focus_in)
        self.entry_search.bind('<FocusOut>', self._on_search_focus_out)
        self.entry_search.bind("<Return>", lambda e: self.load_directory(self.current_dir))
        # Bug 10 fix: debounce search so it waits 300ms after last keystroke before reloading
        self._search_after_id = None
        self.entry_search.bind("<KeyRelease>", self._on_search_key_release)

        # Go Button
        btn_go = ttk.Button(top_bar, text="Ir ➔", width=6, command=lambda: self.go_to_path(self.path_var.get()), style='Accent.TButton')
        btn_go.pack(side=tk.LEFT, padx=10, pady=10)

        self.preview_visible = True
        self.btn_preview_toggle = ttk.Button(top_bar, text="◫ Ocultar vista", command=self.toggle_preview_panel)
        self.btn_preview_toggle.pack(side=tk.RIGHT, padx=(0, 10), pady=10)

        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        open_as_menu = tk.Menu(file_menu, tearoff=0)
        open_as_menu.add_command(label="Texto", command=self.action_open_selected_as_text)
        open_as_menu.add_command(label="Binario / Hex", command=self.action_open_selected_as_binary)
        open_as_menu.add_command(label="PDF", command=self.action_open_selected_as_pdf)
        file_menu.add_command(label="Nuevo archivo", command=self.action_touch)
        file_menu.add_command(label="Nueva carpeta", command=self.action_mkdir)
        file_menu.add_separator()
        file_menu.add_command(label="Abrir seleccionado", command=self.action_edit_file)
        file_menu.add_cascade(label="Abrir como", menu=open_as_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Recargar", command=self.refresh)
        file_menu.add_command(label="Salir", command=self.destroy)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Mostrar / ocultar vista previa", command=self.toggle_preview_panel)

        menubar.add_cascade(label="Archivo", menu=file_menu)
        menubar.add_cascade(label="Vista", menu=view_menu)
        self.config(menu=menubar)

        # --- Main Layout Splitter ---
        main_pane = ttk.PanedWindow(self.root_frame, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # 1. Left Sidebar (Bookmarks / Directory tree shortcuts)
        sidebar = ttk.Frame(main_pane, width=180, style='Card.TFrame')
        sidebar.pack(fill=tk.BOTH, expand=True)
        main_pane.add(sidebar)
        
        lbl_shortcuts = ttk.Label(sidebar, text="ACCESOS RÁPIDOS", style='Section.TLabel')
        lbl_shortcuts.pack(anchor='w', padx=15, pady=(15, 5))

        shortcuts_frame = ttk.Frame(sidebar, style='Card.TFrame')
        shortcuts_frame.pack(fill=tk.X, padx=10)

        # Sidebar Shortcuts buttons
        def make_shortcut(name, path_getter):
            btn = ttk.Button(shortcuts_frame, text=name)
            btn.configure(command=lambda: self.go_to_path(path_getter()))
            btn.pack(fill=tk.X, pady=2)
            
            # Hover effect
            

        make_shortcut("📁 Espacio Trabajo", lambda: os.getcwd())
        make_shortcut("🏠 Inicio (Home)", lambda: os.path.expanduser("~"))
        make_shortcut("🖥️ Escritorio", lambda: os.path.join(os.path.expanduser("~"), "Desktop"))
        make_shortcut("📄 Documentos", lambda: os.path.join(os.path.expanduser("~"), "Documents"))

        # 2. Center File list + preview
        center_frame = ttk.Frame(main_pane, style='Card.TFrame')
        main_pane.add(center_frame)

        # File List Actions Header (Touch, Mkdir, Open Terminal)
        actions_header = ttk.Frame(center_frame, style='Card.TFrame')
        actions_header.pack(fill=tk.X, padx=10, pady=5)
        
        btn_new_file = ttk.Button(actions_header, text="📄 Nuevo Archivo", command=self.action_touch)
        btn_new_file.pack(side=tk.LEFT, padx=5)

        btn_new_folder = ttk.Button(actions_header, text="📁 Nueva Carpeta", command=self.action_mkdir)
        btn_new_folder.pack(side=tk.LEFT, padx=5)

        # Mejora 3: Open Terminal button (Windows only)
        if sys.platform == 'win32':
            btn_terminal = ttk.Button(actions_header, text="⚡ Terminal", command=self.action_open_terminal)
            btn_terminal.pack(side=tk.LEFT, padx=5)

        self.center_content = ttk.Frame(center_frame, style='Card.TFrame')
        self.center_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # File Treeview area
        tree_frame = ttk.Frame(self.center_content, style='Card.TFrame', width=460)
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Preview panel for the selected file or folder
        self.preview_frame = ttk.Frame(self.center_content, style='Card.TFrame', width=390, padding=12)
        self.preview_frame.pack_propagate(False)

        ttk.Label(self.preview_frame, text="VISTA PREVIA", style='Section.TLabel').pack(anchor='w', pady=(0, 8))
        self.preview_header = ttk.Label(self.preview_frame, text="Selecciona un archivo o carpeta", style='CardTitle.TLabel', wraplength=340, justify='left')
        self.preview_header.pack(anchor='w', pady=(0, 4))
        self.preview_meta = ttk.Label(self.preview_frame, text="", style='CardSubtitle.TLabel', wraplength=340, justify='left')
        self.preview_meta.pack(anchor='w', pady=(0, 10))

        preview_actions = ttk.Frame(self.preview_frame, style='Card.TFrame')
        preview_actions.pack(fill=tk.X, pady=(0, 10))
        self.btn_preview_copy = ttk.Button(preview_actions, text="Copiar ruta", command=self.copy_selected_path)
        self.btn_preview_copy.pack(side=tk.LEFT)
        self.btn_preview_open = ttk.Button(preview_actions, text="Abrir editor", command=self.action_edit_file, style='Accent.TButton')
        self.btn_preview_open.pack(side=tk.RIGHT)

        preview_body = ttk.Frame(self.preview_frame, style='Card.TFrame')
        preview_body.pack(fill=tk.BOTH, expand=True)

        cols = ('name', 'type', 'size', 'mtime', 'ctime')
        self.tree = ttk.Treeview(tree_frame, columns=cols, show='headings', selectmode='browse')
        
        self.tree.heading('name', text='Nombre', anchor='w')
        self.tree.heading('type', text='Tipo', anchor='w')
        self.tree.heading('size', text='Tamaño', anchor='e')
        self.tree.heading('mtime', text='Modificado', anchor='w')
        self.tree.heading('ctime', text='Creado', anchor='w')

        self.tree.column('name', width=220, anchor='w')
        self.tree.column('type', width=90, anchor='w')
        self.tree.column('size', width=90, anchor='e')
        self.tree.column('mtime', width=140, anchor='w')
        self.tree.column('ctime', width=140, anchor='w')

        # Treeview scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.preview_text = tk.Text(preview_body, font=('Consolas', 10), wrap=tk.NONE)
        style_modern_text(self.preview_text, wrap=tk.NONE)
        self.preview_text.configure(
            bg=INPUT_BG,
            fg=TEXT_PRIMARY,
            insertbackground=TEXT_PRIMARY,
            highlightbackground=BORDER_BG,
            highlightcolor=ACCENT,
            selectbackground=ACCENT,
            selectforeground=ON_ACCENT,
            relief='flat',
            bd=0,
        )
        self.preview_text.configure(takefocus=0, cursor='arrow')
        self.preview_text.bind('<Key>', lambda e: 'break')
        self.preview_text.bind('<<Paste>>', lambda e: 'break')
        self.preview_text.bind('<Control-v>', lambda e: 'break')
        self.preview_text.bind('<Control-V>', lambda e: 'break')
        self.preview_text.bind('<Control-a>', lambda e: 'break')
        self.preview_text.bind('<Control-A>', lambda e: 'break')
        self.preview_text.bind('<Control-c>', lambda e: 'break')
        self.preview_text.bind('<Control-C>', lambda e: 'break')
        preview_vscroll = ttk.Scrollbar(preview_body, orient=tk.VERTICAL, command=self.preview_text.yview)
        preview_hscroll = ttk.Scrollbar(preview_body, orient=tk.HORIZONTAL, command=self.preview_text.xview)
        self.preview_text.configure(yscrollcommand=preview_vscroll.set, xscrollcommand=preview_hscroll.set)
        preview_body.columnconfigure(0, weight=1)
        preview_body.rowconfigure(0, weight=1)
        self.preview_text.grid(row=0, column=0, sticky='nsew')
        preview_vscroll.grid(row=0, column=1, sticky='ns')
        preview_hscroll.grid(row=1, column=0, sticky='ew')

        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
        self.tree.bind("<Double-1>", self.on_item_double_click)
        # Context menu (right click)
        self.tree.bind("<Button-3>", self.on_tree_right_click)

        # Keyboard shortcuts
        self.bind('<Control-r>', lambda e: (self.refresh(), "break"))
        self.bind('<Control-n>', lambda e: (self.action_touch(), "break"))
        self.bind('<Control-Shift-N>', lambda e: (self.action_mkdir(), "break"))
        self.bind('<Control-f>', lambda e: (self.entry_search.focus_set(), "break"))

        if self.preview_visible:
            self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))

        # 3. Right Details & Actions Panel
        right_panel = ttk.Frame(main_pane, width=280, style='Card.TFrame')
        right_panel.pack(fill=tk.BOTH, expand=True)
        main_pane.add(right_panel)

        self.setup_right_panel(right_panel)

        # --- Bottom Status Console Log ---
        self.status_bar = tk.Text(self.root_frame, height=4, font=('Consolas', 9), padx=10, pady=5)
        style_modern_text(self.status_bar, readonly=True)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_status("Aplicación PyFSManager iniciada.")

    def setup_right_panel(self, parent):
        # Scrollable container for details panel in case screen is small
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

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

        # --- Estilo React-like: Tarjetas (Cards) para organizar contenido ---
        card_detalles = ttk.Frame(scroll_frame, style='Card.TFrame', padding=14)
        card_detalles.pack(fill=tk.X, padx=15, pady=(15, 5))
        
        ttk.Label(card_detalles, text="DETALLES", style='Section.TLabel').pack(anchor='w', pady=(0, 10))
        
        self.lbl_name = ttk.Label(card_detalles, text="Ningún elemento seleccionado", style='CardTitle.TLabel', wraplength=230, justify='left')
        self.lbl_name.pack(anchor='w', pady=(0, 5))
        
        self.lbl_type = ttk.Label(card_detalles, text="Tipo: -", style='CardSubtitle.TLabel')
        self.lbl_type.pack(anchor='w', pady=2)
        
        self.lbl_nlink = ttk.Label(card_detalles, text="Hard links: -", style='CardSubtitle.TLabel')
        self.lbl_nlink.pack(anchor='w', pady=2)
        
        self.lbl_size = ttk.Label(card_detalles, text="Tamaño: -", style='CardSubtitle.TLabel')
        self.lbl_size.pack(anchor='w', pady=2)
        
        self.lbl_link = ttk.Label(card_detalles, text="", style='CardSubtitle.TLabel', wraplength=230, justify='left')
        self.lbl_link.pack(anchor='w', pady=2)

        card_tiempos = ttk.Frame(scroll_frame, style='Card.TFrame', padding=14)
        card_tiempos.pack(fill=tk.X, padx=15, pady=5)
        
        ttk.Label(card_tiempos, text="MARCAS DE TIEMPO", style='Section.TLabel').pack(anchor='w', pady=(0, 10))
        
        times_grid = ttk.Frame(card_tiempos, style='Card.TFrame')
        times_grid.pack(fill=tk.X)
        
        # Grid layout for perfect alignment
        ttk.Label(times_grid, text="Acceso:", style='CardSubtitle.TLabel').grid(row=0, column=0, sticky='w', pady=2, padx=(0, 10))
        self.lbl_atime = ttk.Label(times_grid, text="-", style='CardValue.TLabel')
        self.lbl_atime.grid(row=0, column=1, sticky='w', pady=2)
        
        ttk.Label(times_grid, text="Modif:", style='CardSubtitle.TLabel').grid(row=1, column=0, sticky='w', pady=2, padx=(0, 10))
        self.lbl_mtime = ttk.Label(times_grid, text="-", style='CardValue.TLabel')
        self.lbl_mtime.grid(row=1, column=1, sticky='w', pady=2)
        
        ttk.Label(times_grid, text="Cambio:", style='CardSubtitle.TLabel').grid(row=2, column=0, sticky='w', pady=2, padx=(0, 10))
        self.lbl_ctime = ttk.Label(times_grid, text="-", style='CardValue.TLabel')
        self.lbl_ctime.grid(row=2, column=1, sticky='w', pady=2)
        
        ttk.Label(times_grid, text="Creado:", style='CardSubtitle.TLabel').grid(row=3, column=0, sticky='w', pady=2, padx=(0, 10))
        self.lbl_birth = ttk.Label(times_grid, text="-", style='CardValue.TLabel')
        self.lbl_birth.grid(row=3, column=1, sticky='w', pady=2)

        self.btn_edit_times = ttk.Button(card_tiempos, text="⏱ Editar Tiempos", command=self.action_edit_times, state=tk.DISABLED, style='Accent.TButton')
        self.btn_edit_times.pack(anchor='w', pady=(10, 0))

        # --- Section: Permisos ---
        card_perms = ttk.Frame(scroll_frame, style='Card.TFrame', padding=14)
        card_perms.pack(fill=tk.X, padx=15, pady=5)
        ttk.Label(card_perms, text="PERMISOS (POSIX/ACL)", style='Section.TLabel').pack(anchor='w', pady=(0, 10))
        
        perms_frame = ttk.Frame(card_perms, style='Card.TFrame')
        perms_frame.pack(fill=tk.X)

        # Header Row
        ttk.Label(perms_frame, text="Rol", style='CardSubtitle.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(perms_frame, text="R", style='CardSubtitle.TLabel').grid(row=0, column=1, padx=5)
        ttk.Label(perms_frame, text="W", style='CardSubtitle.TLabel').grid(row=0, column=2, padx=5)
        ttk.Label(perms_frame, text="X", style='CardSubtitle.TLabel').grid(row=0, column=3, padx=5)

        # Variables for checkboxes
        self.chk_vars = {
            'u': [tk.BooleanVar(value=False) for _ in range(3)],
            'g': [tk.BooleanVar(value=False) for _ in range(3)],
            'o': [tk.BooleanVar(value=False) for _ in range(3)]
        }

        # Checkboxes
        roles = [('Usuario (u)', 'u', 1), ('Grupo (g)', 'g', 2), ('Otros (o)', 'o', 3)]
        for label, key, row in roles:
            ttk.Label(perms_frame, text=label, style='CardSubtitle.TLabel').grid(row=row, column=0, sticky='w', pady=2)
            for i in range(3):
                chk = ttk.Checkbutton(
                    perms_frame, 
                    variable=self.chk_vars[key][i]
                )
                chk.grid(row=row, column=i+1, pady=2)

        self.btn_apply_perms = ttk.Button(card_perms, text="✓ Aplicar Permisos", command=self.action_apply_permissions, state=tk.DISABLED, style='Accent.TButton')
        self.btn_apply_perms.pack(anchor='w', pady=(10, 0))

        # --- Section: Acciones ---
        card_acciones = ttk.Frame(scroll_frame, style='Card.TFrame', padding=14)
        card_acciones.pack(fill=tk.X, padx=15, pady=5)
        ttk.Label(card_acciones, text="ACCIONES", style='Section.TLabel').pack(anchor='w', pady=(0, 10))
        
        actions_grid = ttk.Frame(card_acciones, style='Card.TFrame')
        actions_grid.pack(fill=tk.X)

        self.btn_copy = ttk.Button(actions_grid, text="📄 Copiar", command=self.action_copy, state=tk.DISABLED)
        self.btn_copy.grid(row=0, column=0, padx=2, pady=4, sticky='ew')
        
        self.btn_move = ttk.Button(actions_grid, text="➔ Mover", command=self.action_move, state=tk.DISABLED)
        self.btn_move.grid(row=0, column=1, padx=2, pady=4, sticky='ew')

        self.btn_rename = ttk.Button(actions_grid, text="✏ Renombrar", command=self.action_rename, state=tk.DISABLED)
        self.btn_rename.grid(row=1, column=0, padx=2, pady=4, sticky='ew')
        
        self.btn_delete = ttk.Button(actions_grid, text="🗑 Eliminar", command=self.action_delete, state=tk.DISABLED)
        self.btn_delete.grid(row=1, column=1, padx=2, pady=4, sticky='ew')

        self.btn_link = ttk.Button(card_acciones, text="🔗 Crear Enlace (Link)", command=self.action_create_link, state=tk.DISABLED, style='Accent.TButton')
        self.btn_link.pack(anchor='w', fill=tk.X, pady=(5,0))

        actions_grid.columnconfigure(0, weight=1)
        actions_grid.columnconfigure(1, weight=1)

    def copy_selected_path(self):
        if not self.selected_item:
            return
        self.clipboard_clear()
        self.clipboard_append(self.selected_item)
        self.log_status(f"Ruta copiada: {self.selected_item}")

    def toggle_preview_panel(self):
        if not hasattr(self, 'preview_frame'):
            return
        if self.preview_visible:
            self.preview_frame.pack_forget()
            self.btn_preview_toggle.configure(text="◫ Mostrar vista")
        else:
            self.preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
            self.preview_frame.pack_propagate(False)
            self.btn_preview_toggle.configure(text="◫ Ocultar vista")
        self.preview_visible = not self.preview_visible

    def clear_preview(self, message: str = "Selecciona un archivo o carpeta"):
        if not hasattr(self, 'preview_header'):
            return
        self.preview_header.configure(text=message)
        self.preview_meta.configure(text="")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert(tk.END, "La vista previa aparecerá aquí.\n\nTip: usa doble clic para abrir archivos o Enter para entrar en carpetas.")

    def update_preview(self, meta: Optional[FileMetadata], error_message: Optional[str] = None):
        if not hasattr(self, 'preview_header'):
            return

        self.preview_text.delete("1.0", tk.END)

        if error_message:
            self.preview_header.configure(text="No se pudo cargar la vista previa")
            self.preview_meta.configure(text=error_message)
            self.preview_text.insert(tk.END, error_message)
            return

        if not meta:
            self.clear_preview()
            return

        self.preview_header.configure(text=meta.name)
        self.preview_meta.configure(text=f"{meta.type.upper()} · {format_size(meta.size)} · {meta.path}")
        self.btn_preview_copy.configure(state=tk.NORMAL)

        if os.path.isdir(meta.path):
            self.btn_preview_open.configure(text="Entrar carpeta", command=lambda p=meta.path: self.go_to_path(p), state=tk.NORMAL)
        else:
            from .utils import detect_file_type
            if detect_file_type(meta.path) == 'document':
                self.btn_preview_open.configure(text="Abrir externamente", command=lambda p=meta.path: self.action_open_external(p), state=tk.NORMAL)
            else:
                self.btn_preview_open.configure(text="Abrir editor", command=self.action_edit_file, state=tk.NORMAL)

        try:
            if meta.type in ('directory', 'junction'):
                try:
                    entries = list(os.scandir(meta.path))
                    directories = sum(1 for entry in entries if entry.is_dir(follow_symlinks=False))
                    files = sum(1 for entry in entries if entry.is_file(follow_symlinks=False))
                    preview_names = [entry.name for entry in entries[:20]]
                    text = [
                        f"Carpeta: {meta.path}",
                        f"Elementos: {len(entries)}",
                        f"Subcarpetas: {directories}",
                        f"Archivos: {files}",
                        "",
                        "Primeros elementos:",
                    ]
                    text.extend(f"- {name}" for name in preview_names)
                    self.preview_text.insert(tk.END, "\n".join(text))
                except Exception as e:
                    self.preview_text.insert(tk.END, f"No se pudo resumir la carpeta:\n{e}")
            else:
                from .utils import detect_file_type, detect_encoding
                from .cli import hex_dump

                ftype = detect_file_type(meta.path)
                if ftype == 'pdf':
                    try:
                        from pypdf import PdfReader
                        reader = PdfReader(meta.path)
                        pages = []
                        for page in reader.pages[:2]:
                            pages.append(page.extract_text() or "(sin texto extraíble en esta página)")
                        self.preview_text.insert(tk.END, f"PDF · Páginas: {len(reader.pages)}\n\n" + "\n\n--- Página ---\n\n".join(pages))
                    except Exception as e:
                        self.preview_text.insert(tk.END, f"No se pudo leer el PDF:\n{e}")
                    return
                if ftype == 'document':
                    self.preview_text.insert(
                        tk.END,
                        "Formato de documento detectado.\n\n"
                        "PyFSManager no lo renderiza internamente. Usa 'Abrir externamente' para abrirlo con la app predeterminada."
                    )
                    return
                if ftype == 'binary':
                    with open(meta.path, 'rb') as f:
                        data = f.read(1024)
                    self.preview_text.insert(tk.END, "Vista previa binaria (primeros 1024 bytes)\n\n")
                    self.preview_text.insert(tk.END, hex_dump(data, max_bytes=1024))
                else:
                    encoding = detect_encoding(meta.path)
                    with open(meta.path, 'r', encoding=encoding, errors='replace') as f:
                        text = f.read(6000)
                    if not text:
                        text = "(archivo vacío)"
                    self.preview_text.insert(tk.END, text)
                    if meta.size > 6000:
                        self.preview_text.insert(tk.END, f"\n\n... vista previa truncada ({format_size(meta.size)} total) ...")
        except Exception as e:
            self.preview_text.insert(tk.END, f"No se pudo generar la vista previa:\n{e}")

    # --- UI Logic ---

    def log_status(self, msg: str, is_error: bool = False):
        # Bash Simulation Mode
        if msg.startswith("SHELL_SIMULATE:"):
            content = msg.replace("SHELL_SIMULATE: ", "", 1)
            self.status_bar.configure(state=tk.NORMAL)
            
            import re
            clean_content = re.sub(r'\033\[[0-9;]*m', '', content)
            
            self.status_bar.insert(tk.END, clean_content + "\n")
            self.status_bar.see(tk.END)
            self.status_bar.configure(state=tk.DISABLED)
            return

        # Handle Syscall Logs (format as comments or hidden in shell view)
        if " | Syscall: " in msg:
            # Format: # [EJECUTANDO] <cmd> | Syscall: <syscall>
            # To make it look like a shell comment/debug line
            self.status_bar.configure(state=tk.NORMAL)
            self.status_bar.insert(tk.END, f"# [DEBUG] {msg}\n")
            self.status_bar.see(tk.END)
            self.status_bar.configure(state=tk.DISABLED)
            return

        # Ignore redundant "OK" logs if we're in shell mode
        if msg.startswith("Directorio cargado:") or msg.startswith("Listing directory:"):
            return

        t_str = time.strftime("%H:%M:%S")
        prefix = f"[{t_str}] [ERROR] " if is_error else f"[{t_str}] [OK] "
        
        self.status_bar.configure(state=tk.NORMAL)
        self.status_bar.insert(tk.END, prefix + msg + "\n")
        self.status_bar.see(tk.END)
        self.status_bar.configure(state=tk.DISABLED)

    def load_directory(self, path: str, select_path: Optional[str] = None):
        path = os.path.abspath(path)
        try:
            # Check exist and is dir
            if not os.path.exists(path) or not os.path.isdir(path):
                messagebox.showerror("Error", f"La ruta no es un directorio válido: {path}")
                return

            self.current_dir = path
            self.path_var.set(self.current_dir)
            if hasattr(self, 'path_chip'):
                self.path_chip.configure(text=self.current_dir)
            
            # Clear treeview
            for child in self.tree.get_children():
                self.tree.delete(child)

            # Read items
            items = os.listdir(self.current_dir)
            
            # Show shell-like prompt and ls -la output
            username = os.environ.get('USER', 'user')
            hostname = os.uname().nodename if hasattr(os, 'uname') else 'linux'
            # Shorten home path to ~
            home = os.path.expanduser('~')
            display_path = self.current_dir.replace(home, '~') if self.current_dir.startswith(home) else self.current_dir
            
            prompt = f"\033[01;32m{username}@{hostname}\033[00m:\033[01;34m{display_path}\033[00m$ "
            
            try:
                ls_output = FSManager.load_directory_ls(self.current_dir)
                # We use a special marker to tell log_status this is a BASH simulation
                self.log_status(f"SHELL_SIMULATE: {prompt}ls -la\n{ls_output}")
            except Exception as e:
                self.log_status(f"Error generating ls -la: {e}", is_error=True)

            # Retrieve metadata
            item_metas = []
            for item in items:
                p = os.path.join(self.current_dir, item)
                try:
                    # Use silent=True to avoid polluting the terminal with internal stat calls
                    meta = FSManager.get_metadata(p, silent=True)
                    item_metas.append(meta)
                except Exception as e:
                    # Log failures to retrieve metadata but continue listing
                    self.log_status(f"Fallo al obtener metadatos de '{p}': {e}", is_error=True)

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

                # Apply search filter if present, ignoring the placeholder text
                filt = self.filter_var.get().strip().lower()
                if filt and filt != self._search_placeholder.strip().lower() and filt not in meta.name.lower():
                    continue

                display_name = prefix + meta.name
                size_str = format_size(meta.size) if meta.type == 'regular' else '-'
                mtime_str = format_time(meta.mtime)
                ctime_str = format_time(meta.birthtime) if meta.birthtime else format_time(meta.ctime)
                
                self.tree.insert(
                    '', 
                    tk.END, 
                    iid=meta.path, 
                    values=(display_name, meta.type.upper(), size_str, mtime_str, ctime_str)
                )

            # Select item if specified
            if select_path and select_path in self.tree.get_children():
                self.tree.selection_set(select_path)
                self.tree.focus(select_path)
                self.tree.see(select_path)
                self.on_item_select(None)
            else:
                self.clear_selection()

            self.log_status(f"Directorio cargado: {self.current_dir}")
        except Exception as e:
            self.log_status(f"Error al cargar directorio: {e}", is_error=True)
            messagebox.showerror("Error", f"No se pudo cargar el directorio:\n{e}")

    def clear_selection(self):
        self.selected_item = None
        self.selected_meta = None
        
        self.lbl_name.configure(text="Ningún elemento seleccionado")
        self.lbl_type.configure(text="Tipo: -")
        self.lbl_nlink.configure(text="Hard links: -")
        self.lbl_size.configure(text="Tamaño: -")
        self.lbl_link.configure(text="")
        
        self.lbl_atime.configure(text="-")
        self.lbl_mtime.configure(text="-")
        self.lbl_ctime.configure(text="-")
        self.lbl_birth.configure(text="-")

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
        if hasattr(self, 'btn_preview_copy'):
            self.btn_preview_copy.configure(state=tk.DISABLED)
        if hasattr(self, 'btn_preview_open'):
            self.btn_preview_open.configure(state=tk.DISABLED, text="Abrir editor", command=self.action_edit_file)
        self.update_preview(None)

    def on_item_select(self, event):
        selection = self.tree.selection()
        if not selection:
            self.clear_selection()
            return

        filepath = selection[0]
        self.selected_item = filepath

        try:
            # Use silent=True to avoid polluting the terminal with internal stat calls when selecting items
            self.selected_meta = FSManager.get_metadata(filepath, silent=True)
            meta = self.selected_meta
            
            # Update labels
            self.lbl_name.configure(text=meta.name)
            self.lbl_type.configure(text=f"Tipo: {meta.type.upper()}")
            self.lbl_nlink.configure(text=f"Hard links: {meta.nlink}")
            self.lbl_size.configure(text=f"Tamaño: {meta.size} bytes ({format_size(meta.size)})")
            
            if meta.link_target:
                self.lbl_link.configure(text=f"Destino: {meta.link_target}")
            else:
                self.lbl_link.configure(text="")

            self.lbl_atime.configure(text=format_time(meta.atime))
            self.lbl_mtime.configure(text=format_time(meta.mtime))
            self.lbl_ctime.configure(text=format_time(meta.ctime))
            
            if meta.birthtime:
                self.lbl_birth.configure(text=format_time(meta.birthtime))
            else:
                self.lbl_birth.configure(text="N/D")

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

            self.update_preview(meta)
        except Exception as e:
            self.log_status(f"Error al leer metadatos de '{filepath}': {e}", is_error=True)
            self.update_preview(None, error_message=str(e))

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
            from .utils import detect_file_type
            if detect_file_type(self.selected_item) == 'document':
                self.action_open_external(self.selected_item)
            else:
                self.action_edit_file()

    def on_tree_right_click(self, event):
        # Identify the row under cursor
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            self.show_empty_space_context_menu(event)
            return
        # Select it and refresh the detail panel (Bug 7 fix)
        self.tree.selection_set(row_id)
        self.selected_item = row_id
        self.on_item_select(None)  # refresh right-panel details
        try:
            self.selected_meta = FSManager.get_metadata(row_id)
        except Exception:
            self.selected_meta = None

        # Build context menu
        menu = tk.Menu(self, tearoff=0)
        style_modern_menu(menu)
        menu.add_command(label="Abrir / Editar", command=self.action_edit_file)
        menu.add_command(label="Abrir externamente", command=self.action_open_external)
        menu.add_command(label="Copiar", command=self.action_copy)
        menu.add_command(label="Mover", command=self.action_move)
        menu.add_command(label="Renombrar", command=self.action_rename)
        menu.add_separator()
        menu.add_command(label="Propiedades", command=self.action_selected_properties)
        menu.add_separator()
        menu.add_command(label="Eliminar", command=self.action_delete)
        menu.add_separator()
        menu.add_command(label="Crear Enlace...", command=self.action_create_link)

        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def show_empty_space_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        style_modern_menu(menu)
        menu.add_command(label="📄 Nuevo Archivo", command=self.action_touch)
        menu.add_command(label="📁 Nueva Carpeta", command=self.action_mkdir)
        menu.add_separator()
        menu.add_command(label="⟳ Recargar", command=self.refresh)
        menu.add_separator()
        menu.add_command(label="⚙ Propiedades de esta carpeta", command=self.action_current_dir_properties)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def action_current_dir_properties(self):
        try:
            meta = FSManager.get_metadata(self.current_dir)
            
            prop_dialog = tk.Toplevel(self)
            apply_modern_palette(prop_dialog)
            prop_dialog.title(f"Propiedades - {os.path.basename(self.current_dir)}")
            prop_dialog.geometry("460x300")
            prop_dialog.resizable(False, False)
            prop_dialog.transient(self)
            prop_dialog.grab_set()
            
            frame = ttk.Frame(prop_dialog, style='TFrame', padding=16)
            frame.pack(fill=tk.BOTH, expand=True)
            
            header = ttk.Frame(frame, style='Card.TFrame', padding=(16, 12))
            header.pack(fill=tk.X, pady=(0, 12))

            ttk.Label(header, text="Propiedades de la carpeta", style='CardTitle.TLabel').pack(anchor='w')
            ttk.Label(header, text=f"📁 {os.path.basename(self.current_dir)}", style='CardSubtitle.TLabel').pack(anchor='w', pady=(4, 0))
            
            grid = ttk.Frame(frame, style='Card.TFrame', padding=14)
            grid.pack(fill=tk.X)
            
            ttk.Label(grid, text="Ruta:", style='CardSubtitle.TLabel').grid(row=0, column=0, sticky='w', pady=5, padx=(0,10))
            path_lbl = ttk.Label(grid, text=self.current_dir, style='CardValue.TLabel', wraplength=310)
            path_lbl.grid(row=0, column=1, sticky='w', pady=5)
            
            ttk.Label(grid, text="Tamaño:", style='CardSubtitle.TLabel').grid(row=1, column=0, sticky='w', pady=5, padx=(0,10))
            ttk.Label(grid, text=format_size(meta.size), style='CardValue.TLabel').grid(row=1, column=1, sticky='w', pady=5)
            
            ttk.Label(grid, text="Modificado:", style='CardSubtitle.TLabel').grid(row=2, column=0, sticky='w', pady=5, padx=(0,10))
            ttk.Label(grid, text=format_time(meta.mtime), style='CardValue.TLabel').grid(row=2, column=1, sticky='w', pady=5)

            ttk.Label(grid, text="Tipo:", style='CardSubtitle.TLabel').grid(row=3, column=0, sticky='w', pady=5, padx=(0,10))
            ttk.Label(grid, text=meta.type.upper(), style='CardValue.TLabel').grid(row=3, column=1, sticky='w', pady=5)

            button_row = ttk.Frame(frame, style='TFrame')
            button_row.pack(fill=tk.X, pady=(14, 0))

            def copy_current_path():
                self.clipboard_clear()
                self.clipboard_append(self.current_dir)
                self.log_status(f"Ruta copiada al portapapeles: {self.current_dir}")

            ttk.Button(button_row, text="Copiar ruta", command=copy_current_path).pack(side=tk.LEFT)
            
            ttk.Button(button_row, text="Cerrar", command=prop_dialog.destroy, style='Accent.TButton').pack(side=tk.RIGHT)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron obtener las propiedades:\n{e}")

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

    def _on_search_key_release(self, event):
        """Debounce search: wait 300 ms after last keystroke before reloading directory."""
        if self._search_after_id is not None:
            self.after_cancel(self._search_after_id)
        self._search_after_id = self.after(300, lambda: self.load_directory(self.current_dir))

    def _on_search_focus_in(self, event):
        """Clear placeholder text when search entry gains focus."""
        if self.filter_var.get() == self._search_placeholder:
            self.entry_search.delete(0, tk.END)
            self.entry_search.configure(fg=TEXT_PRIMARY)

    def _on_search_focus_out(self, event):
        """Restore placeholder text when search entry loses focus and is empty."""
        if not self.filter_var.get().strip():
            self.entry_search.insert(0, self._search_placeholder)
            self.entry_search.configure(fg=MUTED)

    # --- Actions ---

    def action_touch(self):
        from tkinter import simpledialog
        filename = simpledialog.askstring(
            "Crear Nuevo Archivo",
            "Nombre del archivo nuevo:",
            initialvalue="nuevo_archivo.txt",
            parent=self,
        )
        if not filename:
            return
        path = os.path.join(self.current_dir, filename.strip())
        try:
            FSManager.touch(path)
            self.log_status(f"Archivo creado: {path}")
            self.load_directory(self.current_dir, select_path=os.path.abspath(path))
        except Exception as e:
            self.log_status(f"Error al crear archivo: {e}", is_error=True)
            messagebox.showerror("Error", f"No se pudo crear el archivo:\n{e}")

    def action_open_terminal(self):
        """Open a PowerShell window in the current directory (Windows only)."""
        import subprocess
        try:
            subprocess.Popen(
                ['powershell.exe', '-NoExit', '-Command',
                 f'Set-Location -LiteralPath "{self.current_dir}"'],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            self.log_status(f"Terminal abierta en: {self.current_dir}")
        except Exception as e:
            self.log_status(f"Error al abrir terminal: {e}", is_error=True)
            messagebox.showerror("Error", f"No se pudo abrir la terminal:\n{e}")

    def action_mkdir(self):
        from tkinter import simpledialog
        foldername = simpledialog.askstring("Nueva Carpeta", "Introduce el nombre de la carpeta:")
        if foldername:
            path = os.path.join(self.current_dir, foldername)
            try:
                FSManager.mkdir(path)
                self.log_status(f"Directorio creado: {path}")
                self.load_directory(self.current_dir, select_path=os.path.abspath(path))
            except Exception as e:
                self.log_status(f"Error al crear directorio: {e}", is_error=True)
                messagebox.showerror("Error", f"No se pudo crear la carpeta:\n{e}")

    def action_edit_file(self, view_mode: str = 'auto'):
        if not self.selected_item:
            return
        
        # Bug fix: Ensure we don't try to open a directory for editing
        if os.path.isdir(self.selected_item):
            self.go_to_path(self.selected_item)
            return

        from .utils import detect_file_type
        if view_mode == 'auto' and detect_file_type(self.selected_item) == 'document':
            self.action_open_external(self.selected_item)
            return
        editor = FileEditorWindow(self, self.selected_item, view_mode=view_mode)
        # Center dialog
        editor.geometry("+%d+%d" % (self.winfo_x() + 100, self.winfo_y() + 50))

    def action_open_selected_as_text(self):
        self.action_edit_file('text')

    def action_open_selected_as_binary(self):
        self.action_edit_file('binary')

    def action_open_selected_as_pdf(self):
        self.action_edit_file('pdf')

    def action_open_external(self, path: Optional[str] = None):
        target = os.path.abspath(path or self.selected_item or "")
        if not target:
            return
        try:
            if sys.platform == 'win32':
                os.startfile(target)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', target])
            self.log_status(f"Abierto externamente: {target}")
        except Exception as e:
            self.log_status(f"No se pudo abrir externamente: {e}", is_error=True)
            messagebox.showerror("Error", f"No se pudo abrir el archivo con la aplicación predeterminada:\n{e}")

    def action_selected_properties(self):
        if not self.selected_item:
            return
        try:
            meta = FSManager.get_metadata(self.selected_item)

            prop_dialog = tk.Toplevel(self)
            apply_modern_palette(prop_dialog)
            prop_dialog.title(f"Propiedades - {meta.name}")
            prop_dialog.geometry("500x330")
            prop_dialog.resizable(False, False)
            prop_dialog.transient(self)
            prop_dialog.grab_set()

            frame = ttk.Frame(prop_dialog, style='TFrame', padding=16)
            frame.pack(fill=tk.BOTH, expand=True)

            header = ttk.Frame(frame, style='Card.TFrame', padding=(16, 12))
            header.pack(fill=tk.X, pady=(0, 12))

            ttk.Label(header, text="Propiedades del archivo", style='CardTitle.TLabel').pack(anchor='w')
            ttk.Label(header, text=meta.name, style='CardSubtitle.TLabel').pack(anchor='w', pady=(4, 0))

            grid = ttk.Frame(frame, style='Card.TFrame', padding=14)
            grid.pack(fill=tk.X)

            rows = [
                ("Ruta:", self.selected_item),
                ("Tipo:", meta.type.upper()),
                ("Tamaño:", format_size(meta.size)),
                ("Modificado:", format_time(meta.mtime)),
                ("Creado:", format_time(meta.birthtime) if meta.birthtime else "N/D"),
                ("Hard links:", str(meta.nlink)),
            ]
            if meta.link_target:
                rows.append(("Destino:", meta.link_target))

            for row_index, (label_text, value_text) in enumerate(rows):
                ttk.Label(grid, text=label_text, style='CardSubtitle.TLabel').grid(row=row_index, column=0, sticky='w', pady=5, padx=(0,10))
                ttk.Label(grid, text=value_text, style='CardValue.TLabel', wraplength=360, justify='left').grid(row=row_index, column=1, sticky='w', pady=5)

            button_row = ttk.Frame(frame, style='TFrame')
            button_row.pack(fill=tk.X, pady=(14, 0))

            ttk.Button(button_row, text="Abrir externamente", command=lambda: self.action_open_external(self.selected_item)).pack(side=tk.LEFT)
            ttk.Button(button_row, text="Cerrar", command=prop_dialog.destroy, style='Accent.TButton').pack(side=tk.RIGHT)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron obtener las propiedades del archivo:\n{e}")

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
            self.log_status(f"Permisos aplicados a '{self.selected_item}': {perms.to_symbolic}")
            self.refresh()
            # Select item again to reload display
            self.tree.selection_set(self.selected_item)
        except Exception as e:
            self.log_status(f"Error al aplicar permisos: {e}", is_error=True)
            messagebox.showerror("Error", f"No se pudieron cambiar los permisos:\n{e}")

    def action_copy(self):
        if not self.selected_item:
            return
        if self.selected_meta and self.selected_meta.type in ('directory', 'junction'):
            dialog = CustomFileDialog(self, os.path.dirname(self.selected_item), title="Copiar carpeta a...", mode='directory')
            dst = dialog.result
        else:
            dialog = CustomFileDialog(self, self.current_dir, title="Copiar elemento a...", mode='saveas', initialfile=os.path.basename(self.selected_item))
            dst = dialog.result
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
        dialog = CustomFileDialog(self, self.current_dir, title="Mover elemento a...", mode='saveas', initialfile=os.path.basename(self.selected_item))
        dst = dialog.result
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
