import re

def refactor_gui(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add import sv_ttk and call it in PyFSApp
    if 'import sv_ttk' not in content:
        content = content.replace('import tkinter as tk', 'import tkinter as tk\nimport sv_ttk')
        
    app_init = '''class PyFSApp(tk.Tk):
    """
    Main PyFSManager GUI Application.
    """
    def __init__(self):
        super().__init__()
        sv_ttk.set_theme("dark")'''
    content = re.sub(r'class PyFSApp\(tk\.Tk\):\s+"""\s+Main PyFSManager GUI Application\.\s+"""\s+def __init__\(self\):\s+super\(\)\.__init__\(\)', app_init, content)

    # 2. Remove all bg=..., fg=..., background=..., foreground=...
    content = re.sub(r',\s*bg=[^,)]+', '', content)
    content = re.sub(r',\s*fg=[^,)]+', '', content)
    content = re.sub(r',\s*background=[^,)]+', '', content)
    content = re.sub(r',\s*foreground=[^,)]+', '', content)
    content = re.sub(r'bg=[^,)]+,\s*', '', content)
    content = re.sub(r'fg=[^,)]+,\s*', '', content)

    # 3. Remove .configure(bg=...) etc.
    content = re.sub(r'\.configure\([^)]*bg=[^)]*\)', '', content)
    
    # 4. Replace tk.Frame with ttk.Frame
    content = content.replace('tk.Frame', 'ttk.Frame')
    
    # 5. Replace tk.Label with ttk.Label
    content = content.replace('tk.Label', 'ttk.Label')
    
    # 6. Replace tk.Checkbutton with ttk.Checkbutton
    content = content.replace('tk.Checkbutton', 'ttk.Checkbutton')
    content = content.replace('selectcolor=THEME_BG', '')

    # 7. Simplify setup_styles
    setup_styles_new = '''    def setup_styles(self):
        # sv_ttk handles most styling natively. We just add minor custom font configs if needed.
        pass'''
    content = re.sub(r'    def setup_styles\(self\):.*?    def setup_ui\(self\):', setup_styles_new + '\n\n    def setup_ui(self):', content, flags=re.DOTALL)

    # 8. Button Hover effect removal (no longer needed for modern themes)
    hover_effect = r'btn\.bind\("<Enter>".*?btn\.bind\("<Leave>".*?\)'
    content = re.sub(hover_effect, '', content, flags=re.DOTALL)
    
    # 9. Clean up empty configs
    content = content.replace(', )', ')')
    content = content.replace('(, ', '(')
    content = content.replace(', ,', ',')
    content = content.replace('()', '') # For empty configures

    # 10. Update tk.Button to ttk.Button
    content = content.replace('tk.Button', 'ttk.Button')

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Refactored GUI styling.")

if __name__ == "__main__":
    refactor_gui('pyfsmanager/gui.py')
