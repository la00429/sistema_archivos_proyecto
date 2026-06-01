import tempfile
import os
import traceback

from pyfsmanager.manager import FSManager

print('Python', os.sys.version)

# Create temp file without spaces
f = tempfile.NamedTemporaryFile(delete=False)
path = f.name
f.close()
print('Temp file:', path)

# Test cases
cases = ["755", "rwxr-xr-x", "u+w,g-r", "u+r"]

for c in cases:
    print('\nTrying:', c)
    try:
        FSManager.set_permissions(path, c)
        perms = FSManager.get_metadata(path).permissions
        print('Success ->', perms.to_symbolic(), oct(perms.to_octal()))
    except Exception as e:
        print('Error:')
        traceback.print_exc()

# Now try a path with spaces
dir_with_space = os.path.join(tempfile.gettempdir(), 'dir with space')
os.makedirs(dir_with_space, exist_ok=True)
path2 = os.path.join(dir_with_space, 'file name.txt')
with open(path2, 'w') as f2:
    f2.write('x')

print('\nTemp file with spaces:', path2)
for c in ['755', 'rwxr-xr-x']:
    print('\nTrying on spaced path:', c)
    try:
        FSManager.set_permissions(path2, c)
        perms = FSManager.get_metadata(path2).permissions
        print('Success ->', perms.to_symbolic(), oct(perms.to_octal()))
    except Exception as e:
        print('Error:')
        traceback.print_exc()

print('\nDone')
