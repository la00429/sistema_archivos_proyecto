import re

def fix_parentheses(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Restore lost parentheses
    content = content.replace('super().__init__\n', 'super().__init__()\n')
    content = content.replace('self.setup_styles\n', 'self.setup_styles()\n')
    content = content.replace('self.setup_ui\n', 'self.setup_ui()\n')
    content = content.replace('os.getcwd\n', 'os.getcwd()\n')
    content = content.replace('os.getcwd)', 'os.getcwd())')
    content = content.replace('self.path_var.get)', 'self.path_var.get())')
    content = content.replace('self.path_var.get\n', 'self.path_var.get()\n')
    content = content.replace('self.refresh\n', 'self.refresh()\n')
    content = content.replace('self.on_create\n', 'self.on_create()\n')
    content = content.replace('self.destroy\n', 'self.destroy()\n')
    content = content.replace('self\n', '\n') # self on a line by itself
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed parentheses.")

if __name__ == "__main__":
    fix_parentheses('pyfsmanager/gui.py')
