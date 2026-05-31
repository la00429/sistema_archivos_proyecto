import re
import os

def repair_gui(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Main frame wrapping
    if 'self.root_frame = ttk.Frame(self)' not in content:
        content = content.replace(
            'def setup_ui(self):\n        # --- Top Menu & Address Bar ---',
            'def setup_ui(self):\n        self.root_frame = ttk.Frame(self)\n        self.root_frame.pack(fill=tk.BOTH, expand=True)\n        # --- Top Menu & Address Bar ---'
        )
        # We also need to change top level widgets packed in `self` to `self.root_frame`.
        content = content.replace('ttk.Frame(self,', 'ttk.Frame(self.root_frame,')
        content = content.replace('tk.PanedWindow(self,', 'ttk.PanedWindow(self.root_frame,')
        content = content.replace('tk.Text(self,', 'tk.Text(self.root_frame,')

    # 2. Fix PanedWindow
    content = content.replace('tk.PanedWindow', 'ttk.PanedWindow')

    # 3. Fix Button args in make_shortcut (ttk.Button doesn't support relief, bd, padx, pady inside constructor)
    bad_btn = r"btn = ttk\.Button\(\s*shortcuts_frame,\s*text=name,\s*anchor='w',\s*relief=tk\.FLAT,\s*bd=0,\s*padx=10,\s*pady=6,\s*font=\('Segoe UI',\s*10\),\s*activebackground=ACCENT,\s*activeforeground=ON_ACCENT\s*\)"
    good_btn = "btn = ttk.Button(shortcuts_frame, text=name)"
    content = re.sub(bad_btn, good_btn, content, flags=re.DOTALL)
    
    # 4. Canvas styling (sv_ttk doesn't auto-style Canvas completely)
    content = content.replace('tk.Canvas(parent, bd=0, highlightthickness=0)', "tk.Canvas(parent, bd=0, highlightthickness=0, bg='#1c1c1c')")
    
    # 5. Fix Text widget (sv_ttk doesn't auto-style tk.Text)
    content = content.replace('self.status_bar = tk.Text(self.root_frame, height=4, font=(\'Consolas\', 9), padx=10, pady=5)',
                              "self.status_bar = tk.Text(self.root_frame, height=4, font=('Consolas', 9), padx=10, pady=5, bg='#1c1c1c', fg='#cccccc', bd=0)")
    
    # Text area in FileEditorWindow
    content = content.replace("self.txt_area = tk.Text(\n            self, \n            insertbackground=ON_ACCENT,\n            font=('Consolas', 11),\n            wrap=tk.WORD if self.file_type == 'text' else tk.NONE,\n            padx=10,\n            pady=10,\n        )",
                              "self.txt_area = tk.Text(\n            self, \n            font=('Consolas', 11),\n            wrap=tk.WORD if self.file_type == 'text' else tk.NONE,\n            padx=10,\n            pady=10,\n            bg='#1c1c1c', fg='#ffffff', insertbackground='#ffffff', bd=0\n        )")

    # 6. Any other stray tk -> ttk fixes
    content = content.replace('tk.Label(', 'ttk.Label(')
    content = content.replace('ttk.Label(self.root_frame,', 'ttk.Label(self.root_frame,')
    content = content.replace('tk.Frame(', 'ttk.Frame(')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Repaired GUI for sv_ttk.")

if __name__ == "__main__":
    repair_gui('pyfsmanager/gui.py')
