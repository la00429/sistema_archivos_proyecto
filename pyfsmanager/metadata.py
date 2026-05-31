import os
import sys
import stat
import datetime
from .permissions import FilePermissions, get_file_permissions
from .links import is_junction, is_symlink, read_link
import warnings

# Conditionally import Windows dependencies
if sys.platform == 'win32':
    try:
        import win32file
        import win32con
        import pywintypes
        HAS_WIN32 = True
        # Safely define constants if they are not in win32con
        FILE_WRITE_ATTRIBUTES = getattr(win32con, 'FILE_WRITE_ATTRIBUTES', 0x0100)
        FILE_FLAG_BACKUP_SEMANTICS = getattr(win32con, 'FILE_FLAG_BACKUP_SEMANTICS', 0x02000000)
    except ImportError:
        HAS_WIN32 = False
else:
    HAS_WIN32 = False

class FileMetadata:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.name = os.path.basename(path)
        
        # Load filesystem stat
        # If it's a symlink or junction, we stat the link itself (lstat) to get link metadata
        try:
            st = os.lstat(path)
        except OSError as e:
            raise FileNotFoundError(f"Error accessing path {path}: {e}")
            
        self.size = st.st_size
        self.atime = st.st_atime
        self.mtime = st.st_mtime
        self.ctime = st.st_ctime # Linux: change, Windows: creation
        self.nlink = st.st_nlink  # Number of hard links to this inode
        
        # Determine file type
        if is_junction(path):
            self.type = 'junction'
        elif is_symlink(path):
            self.type = 'symlink'
        elif stat.S_ISREG(st.st_mode):
            self.type = 'regular'
        elif stat.S_ISDIR(st.st_mode):
            self.type = 'directory'
        elif stat.S_ISFIFO(st.st_mode):
            self.type = 'fifo'
        elif stat.S_ISSOCK(st.st_mode):
            self.type = 'socket'
        else:
            self.type = 'unknown'

        # Get target if link
        if self.type in ('symlink', 'junction'):
            try:
                self.link_target = read_link(path)
            except Exception:
                self.link_target = None
        else:
            self.link_target = None

        # Permissions (use standard stat mode for permissions, or Windows ACLs)
        try:
            self.permissions = get_file_permissions(path)
        except Exception:
            self.permissions = FilePermissions.from_octal(stat.S_IMODE(st.st_mode))

        # Determine birthtime (creation time)
        self.birthtime = None
        if sys.platform == 'win32':
            # On Windows, ctime is creation time
            self.birthtime = st.st_ctime
        else:
            # On Linux/macOS, check if st_birthtime is available
            if hasattr(st, 'st_birthtime'):
                self.birthtime = st.st_birthtime
            else:
                # Try to use ctime as fallback for birthtime if not available on Linux
                # (Or keep it None, but ctime is a reasonable metadata reference)
                self.birthtime = None

    def to_dict(self) -> dict:
        return {
            'path': self.path,
            'name': self.name,
            'size': self.size,
            'type': self.type,
            'nlink': self.nlink,
            'permissions': self.permissions.to_symbolic(),
            'permissions_octal': oct(self.permissions.to_octal()),
            'atime': datetime.datetime.fromtimestamp(self.atime).isoformat(),
            'mtime': datetime.datetime.fromtimestamp(self.mtime).isoformat(),
            'ctime': datetime.datetime.fromtimestamp(self.ctime).isoformat(),
            'birthtime': datetime.datetime.fromtimestamp(self.birthtime).isoformat() if self.birthtime else None,
            'link_target': self.link_target
        }

    def __repr__(self) -> str:
        return (f"FileMetadata(name='{self.name}', type='{self.type}', size={self.size}, "
                f"nlink={self.nlink}, perms='{self.permissions.to_symbolic()}', mtime={self.mtime})")


def get_metadata(path: str) -> FileMetadata:
    """
    Retrieves the FileMetadata for a given path.
    """
    return FileMetadata(path)


def set_file_times(path: str, atime: float = None, mtime: float = None, birthtime: float = None) -> None:
    """
    Sets the access, modification, and creation (birth) times for a file or directory.
    - atime: Access time (float epoch timestamp)
    - mtime: Modification time (float epoch timestamp)
    - birthtime: Creation time (float epoch timestamp, only fully supported on Windows)
    """
    if not os.path.exists(path) and not os.path.islink(path):
        raise FileNotFoundError(f"Path not found: {path}")

    # If all are None, do nothing
    if atime is None and mtime is None and birthtime is None:
        return

    # Handle birthtime on Windows
    if birthtime is not None and sys.platform == 'win32' and HAS_WIN32:
        try:
            # Open file handle
            handle = win32file.CreateFile(
                path,
                FILE_WRITE_ATTRIBUTES,
                win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE | win32con.FILE_SHARE_DELETE,
                None,
                win32con.OPEN_EXISTING,
                # Directories require FILE_FLAG_BACKUP_SEMANTICS to be opened;
                # regular files use FILE_ATTRIBUTE_NORMAL. The flags must be
                # set as dwFlagsAndAttributes (4th positional arg to CreateFile).
                FILE_FLAG_BACKUP_SEMANTICS if os.path.isdir(path) else win32con.FILE_ATTRIBUTE_NORMAL,
                None
            )
            try:
                def to_pytime(ts):
                    if ts is None:
                        return None
                    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
                    return pywintypes.Time(dt)

                c_time = to_pytime(birthtime)
                a_time = to_pytime(atime)
                m_time = to_pytime(mtime)

                win32file.SetFileTime(handle, c_time, a_time, m_time)
                return  # Windows SetFileTime sets everything, no need to call os.utime
            finally:
                win32file.CloseHandle(handle)
        except Exception as e:
            # Fall back to os.utime for atime/mtime if win32 fails
            warnings.warn(f"win32 SetFileTime falló para '{path}': {e}. Usando os.utime como fallback.")
            

    # If we are on Linux or win32 failed/has no pywin32, we can set atime and mtime
    if atime is not None or mtime is not None:
        # Get current times for fallback
        st = os.stat(path)
        new_atime = atime if atime is not None else st.st_atime
        new_mtime = mtime if mtime is not None else st.st_mtime
        os.utime(path, (new_atime, new_mtime))
        
    if birthtime is not None and sys.platform != 'win32':
        # Emit a warning or ignore
        import warnings
        warnings.warn("Setting birthtime (creation time) is not supported on POSIX systems.")
