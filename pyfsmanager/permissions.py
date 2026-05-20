import os
import sys
import stat

# Conditionally import Windows dependencies
if sys.platform == 'win32':
    try:
        import win32security
        import ntsecuritycon as con
        import win32api
        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False

class FilePermissions:
    def __init__(self, user: str, group: str, other: str):
        """
        Initializes permissions with user, group, and other rwx strings (e.g. "rwx", "r-x", "r--").
        """
        self.user = self._normalize(user)
        self.group = self._normalize(group)
        self.other = self._normalize(other)

    def _normalize(self, rwx: str) -> str:
        r = 'r' if 'r' in rwx else '-'
        w = 'w' if 'w' in rwx else '-'
        x = 'x' if 'x' in rwx else '-'
        return r + w + x

    @classmethod
    def from_octal(cls, mode: int) -> 'FilePermissions':
        """
        Creates FilePermissions from an octal integer (e.g., 0o755).
        """
        user_val = (mode >> 6) & 7
        group_val = (mode >> 3) & 7
        other_val = mode & 7

        def val_to_rwx(val: int) -> str:
            r = 'r' if val & 4 else '-'
            w = 'w' if val & 2 else '-'
            x = 'x' if val & 1 else '-'
            return r + w + x

        return cls(val_to_rwx(user_val), val_to_rwx(group_val), val_to_rwx(other_val))

    @classmethod
    def from_symbolic(cls, mode_str: str) -> 'FilePermissions':
        """
        Creates FilePermissions from a 9-character symbolic string (e.g. "rwxr-xr-x").
        """
        if len(mode_str) != 9:
            raise ValueError("Symbolic permissions string must be 9 characters long.")
        return cls(mode_str[0:3], mode_str[3:6], mode_str[6:9])

    def to_octal(self) -> int:
        """
        Converts to an octal integer.
        """
        def rwx_to_val(rwx: str) -> int:
            val = 0
            if 'r' in rwx: val |= 4
            if 'w' in rwx: val |= 2
            if 'x' in rwx: val |= 1
            return val

        return (rwx_to_val(self.user) << 6) | (rwx_to_val(self.group) << 3) | rwx_to_val(self.other)

    def to_symbolic(self) -> str:
        """
        Converts to a 9-character symbolic string (e.g. "rwxr-xr-x").
        """
        return self.user + self.group + self.other

    def __repr__(self) -> str:
        return f"FilePermissions(user='{self.user}', group='{self.group}', other='{self.other}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, FilePermissions):
            return False
        return self.user == other.user and self.group == other.group and self.other == other.other


def parse_permissions(p, current_octal: int = 0o644) -> FilePermissions:
    """
    Helper function to parse permissions in various formats:
    - FilePermissions object
    - Integer (e.g. 0o755)
    - 9-char symbolic string (e.g. "rwxr-xr-x")
    - Octal string (e.g. "755", "0755", "0o755")
    - chmod symbolic change (e.g. "u+w,g-r")
    """
    if isinstance(p, FilePermissions):
        return p
    if isinstance(p, int):
        return FilePermissions.from_octal(p)
    if isinstance(p, str):
        if len(p) == 9 and not set(p).difference({'-', 'r', 'w', 'x'}):
            return FilePermissions.from_symbolic(p)
        
        # Check if it's an octal representation
        try:
            val = int(p, 8)
            return FilePermissions.from_octal(val)
        except ValueError:
            pass
            
        # Try chmod symbolic command parsing (e.g., "u+rwx")
        try:
            new_octal = parse_chmod_symbolic(current_octal, p)
            return FilePermissions.from_octal(new_octal)
        except Exception as e:
            raise ValueError(f"Unable to parse permissions '{p}': {e}")
            
    raise TypeError(f"Invalid type for permissions: {type(p)}")


def parse_chmod_symbolic(current_mode: int, symbol_str: str) -> int:
    """
    Parses chmod-style symbolic changes (e.g., "u+w,go-rx") and applies them to current_mode.
    """
    mode = current_mode
    for part in symbol_str.split(','):
        if not part:
            continue
            
        if '+' in part:
            who, permissions = part.split('+', 1)
            op = '+'
        elif '-' in part:
            who, permissions = part.split('-', 1)
            op = '-'
        elif '=' in part:
            who, permissions = part.split('=', 1)
            op = '='
        else:
            raise ValueError(f"Missing operator (+, -, =) in '{part}'")
            
        if not who:
            who = 'a'
            
        mask_u = 0
        mask_g = 0
        mask_o = 0
        
        for p in permissions:
            val = 0
            if p == 'r': val = 4
            elif p == 'w': val = 2
            elif p == 'x': val = 1
            else:
                raise ValueError(f"Invalid permission character: {p}")
                
            if 'u' in who or 'a' in who: mask_u |= val
            if 'g' in who or 'a' in who: mask_g |= val
            if 'o' in who or 'a' in who: mask_o |= val
            
        if op == '+':
            mode |= (mask_u << 6) | (mask_g << 3) | mask_o
        elif op == '-':
            mode &= ~((mask_u << 6) | (mask_g << 3) | mask_o)
        elif op == '=':
            clear_mask = 0
            if 'u' in who or 'a' in who: clear_mask |= 0o700
            if 'g' in who or 'a' in who: clear_mask |= 0o070
            if 'o' in who or 'a' in who: clear_mask |= 0o007
            mode &= ~clear_mask
            mode |= (mask_u << 6) | (mask_g << 3) | mask_o
            
    return mode & 0o777


def get_file_permissions(path: str) -> FilePermissions:
    """
    Reads permissions from a file or directory. Handles POSIX and Windows ACLs.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    if sys.platform == 'win32' and HAS_WIN32:
        try:
            return get_windows_permissions(path)
        except Exception:
            # Fall back to standard python stat on failure
            pass

    # POSIX or fallback
    st = os.stat(path)
    mode = stat.S_IMODE(st.st_mode)
    return FilePermissions.from_octal(mode)


def set_file_permissions(path: str, permissions_raw) -> None:
    """
    Sets permissions on a file or directory. Handles POSIX and Windows ACLs.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    # Read current to resolve chmod-like strings relative to current state
    current_permissions = get_file_permissions(path)
    current_octal = current_permissions.to_octal()
    
    perms = parse_permissions(permissions_raw, current_octal)

    if sys.platform == 'win32' and HAS_WIN32:
        try:
            set_windows_permissions(path, perms)
            return
        except Exception:
            # Fall back to standard python chmod on failure
            pass

    # POSIX or fallback
    os.chmod(path, perms.to_octal())


# --- Windows Specific ACL Implementation ---

def get_windows_permissions(path: str) -> FilePermissions:
    # 1. Get security descriptor
    sd = win32security.GetFileSecurity(
        path, 
        win32security.OWNER_SECURITY_INFORMATION | 
        win32security.GROUP_SECURITY_INFORMATION | 
        win32security.DACL_SECURITY_INFORMATION
    )
    owner_sid = sd.GetSecurityDescriptorOwner()
    group_sid = sd.GetSecurityDescriptorGroup()
    everyone_sid = win32security.CreateWellKnownSid(win32security.WinWorldSid)
    dacl = sd.GetSecurityDescriptorDacl()

    if dacl is None:
        # Null DACL means full access to everyone
        return FilePermissions("rwx", "rwx", "rwx")

    owner_rwx = ["-", "-", "-"]
    group_rwx = ["-", "-", "-"]
    everyone_rwx = ["-", "-", "-"]

    # We iterate over ACEs in DACL
    for i in range(dacl.GetAceCount()):
        ace = dacl.GetAce(i)
        ace_type = ace[0][0]
        
        # We only look at allowed permissions for our simple POSIX mapping
        if ace_type != win32security.ACCESS_ALLOWED_ACE_TYPE:
            continue
            
        mask = ace[1]
        sid = ace[2]

        is_owner = (sid == owner_sid)
        is_group = (sid == group_sid)
        is_everyone = (sid == everyone_sid)

        def update_rwx(rwx_list, m):
            if m & con.FILE_GENERIC_READ:
                rwx_list[0] = 'r'
            if m & (con.FILE_GENERIC_WRITE | con.DELETE):
                rwx_list[1] = 'w'
            if m & con.FILE_GENERIC_EXECUTE:
                rwx_list[2] = 'x'

        if is_owner:
            update_rwx(owner_rwx, mask)
        if is_group:
            update_rwx(group_rwx, mask)
        if is_everyone:
            update_rwx(everyone_rwx, mask)

    # Note: If everyone has permissions, by POSIX inheritance logic, we merge Everyone permissions
    # to User and Group as well, since Everyone includes Owner and Group.
    # We do a simple fallback: if Everyone has read, then owner/group also effectively have read.
    for i in range(3):
        if everyone_rwx[i] != '-':
            owner_rwx[i] = everyone_rwx[i]
            group_rwx[i] = everyone_rwx[i]

    # Also, standard Windows files have some default read permissions, let's map at least user read/write
    # if it's not set. If owner_rwx is empty, let's make sure it doesn't look completely empty if we can write to it.
    if "".join(owner_rwx) == "---":
        # Check standard OS access
        if os.access(path, os.R_OK): owner_rwx[0] = 'r'
        if os.access(path, os.W_OK): owner_rwx[1] = 'w'
        if os.access(path, os.X_OK): owner_rwx[2] = 'x'

    return FilePermissions("".join(owner_rwx), "".join(group_rwx), "".join(everyone_rwx))


def set_windows_permissions(path: str, perms: FilePermissions) -> None:
    # 1. Get current security descriptor to extract Owner and Group SIDs
    sd = win32security.GetFileSecurity(
        path, 
        win32security.OWNER_SECURITY_INFORMATION | win32security.GROUP_SECURITY_INFORMATION
    )
    owner_sid = sd.GetSecurityDescriptorOwner()
    group_sid = sd.GetSecurityDescriptorGroup()
    everyone_sid = win32security.CreateWellKnownSid(win32security.WinWorldSid)

    # 2. Build a new DACL
    dacl = win32security.ACL()

    # 3. Helper to map rwx to Windows Generic Rights
    def rwx_to_mask(rwx: str) -> int:
        mask = 0
        if 'r' in rwx:
            mask |= con.FILE_GENERIC_READ
        if 'w' in rwx:
            # We add FILE_GENERIC_WRITE and DELETE so write permission acts like POSIX write (allows modification and deletion)
            mask |= (con.FILE_GENERIC_WRITE | con.DELETE)
        if 'x' in rwx:
            mask |= con.FILE_GENERIC_EXECUTE
        return mask

    owner_mask = rwx_to_mask(perms.user)
    group_mask = rwx_to_mask(perms.group)
    everyone_mask = rwx_to_mask(perms.other)

    is_dir = os.path.isdir(path)
    # Inherit flags for directories
    flags = (win32security.OBJECT_INHERIT_ACE | win32security.CONTAINER_INHERIT_ACE) if is_dir else 0

    # 4. Add ACEs to DACL
    # Order matters: more specific SIDs are usually added first
    if flags:
        dacl.AddAccessAllowedAceEx(win32security.ACL_REVISION, flags, owner_mask, owner_sid)
        dacl.AddAccessAllowedAceEx(win32security.ACL_REVISION, flags, group_mask, group_sid)
        dacl.AddAccessAllowedAceEx(win32security.ACL_REVISION, flags, everyone_mask, everyone_sid)
    else:
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, owner_mask, owner_sid)
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, group_mask, group_sid)
        dacl.AddAccessAllowedAce(win32security.ACL_REVISION, everyone_mask, everyone_sid)

    # 5. Set DACL back to security descriptor and write it to the file
    sd_new = win32security.GetFileSecurity(
        path, 
        win32security.OWNER_SECURITY_INFORMATION | win32security.GROUP_SECURITY_INFORMATION
    )
    sd_new.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(path, win32security.DACL_SECURITY_INFORMATION, sd_new)
