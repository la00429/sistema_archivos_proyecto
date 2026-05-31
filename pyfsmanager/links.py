import os
import sys
import subprocess

def create_hard_link(src: str, dst: str) -> None:
    """
    Creates a hard link pointing to src named dst.
    """
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source file not found: {src}")
    os.link(src, dst)

def create_symbolic_link(src: str, dst: str, is_dir: bool = False) -> None:
    """
    Creates a symbolic link pointing to src named dst.
    On Windows, is_dir specifies whether the target is a directory.
    """
    if sys.platform == 'win32':
        # On Windows, try to auto-detect if src is a directory if is_dir is not specified
        if not is_dir and os.path.isdir(src):
            is_dir = True
        os.symlink(src, dst, target_is_directory=is_dir)
    else:
        os.symlink(src, dst)

def create_junction(src: str, dst: str) -> None:
    """
    Creates a directory junction pointing to src named dst.
    Only supported on Windows. Raises NotImplementedError on Linux.
    """
    if sys.platform != 'win32':
        raise NotImplementedError("Junctions are only supported on Windows.")
        
    if not os.path.isdir(src):
        raise ValueError(f"Junction source must be an existing directory: {src}")
        
    if os.path.exists(dst):
        raise FileExistsError(f"Destination path already exists: {dst}")
        
    # Execute mklink /J. Note that mklink arguments are: link_name target_path
    # We resolve absolute paths to ensure it works correctly
    abs_src = os.path.abspath(src)
    abs_dst = os.path.abspath(dst)
    
    cmd = f'cmd.exe /c mklink /J "{abs_dst}" "{abs_src}"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        raise OSError(f"Failed to create junction: {res.stderr.strip() or res.stdout.strip()}")

def read_link(path: str) -> str:
    """
    Reads the target of a symbolic link or directory junction.
    Cleans up any Windows-specific junction prefixes (e.g. \\??\\).
    """
    if not os.path.exists(path) and not os.path.islink(path):
        raise FileNotFoundError(f"Path not found: {path}")
        
    target = os.readlink(path)
    
    # Clean up Windows junction/symlink prefixes
    if target.startswith('\\??\\'):
        target = target[4:]
    elif target.startswith('\\\\?\\'):
        target = target[4:]
        
    return target

def is_junction(path: str) -> bool:
    """
    Returns True if the path is a directory junction on Windows.
    """
    if sys.platform != 'win32':
        return False
        
    if hasattr(os.path, 'isjunction'):
        return os.path.isjunction(path)
        
    # Fallback for Python < 3.12 (os.path.isjunction was added in 3.12)
    try:
        import win32file
        import win32con
        if os.path.isdir(path):
            attrs = win32file.GetFileAttributes(path)
            return bool(attrs & win32con.FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        pass
    return False

def is_symlink(path: str) -> bool:
    """
    Returns True if the path is a symbolic link (and not a junction).
    """
    if not os.path.islink(path):
        return False
    if sys.platform == 'win32':
        return not is_junction(path)
    return True
