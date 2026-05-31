import re

def fix_gui(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Fix tttk -> ttk
    content = content.replace('tttk.', 'ttk.')
    content = content.replace('ttttk.', 'ttk.')

    # Fix dangling commas
    content = re.sub(r',\s*,', ',', content)
    content = re.sub(r'activebackground=SURFACE,\s*,', '', content)
    content = re.sub(r'activebackground=SURFACE,', '', content)

    # Some widgets might have a stray comma right before closing parenthesis
    content = re.sub(r',\s*\)', ')', content)
    
    # Checkbuttons don't have bd=0 in ttk, it will throw an error
    content = content.replace(', bd=0', '')
    content = content.replace(', bd=0)', ')')

    # Let's fix Treeview selection color since sv_ttk handles it natively
    content = re.sub(r"self\.style\.map\('Treeview'.*?\)", "", content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed GUI syntax.")

if __name__ == "__main__":
    fix_gui('pyfsmanager/gui.py')
