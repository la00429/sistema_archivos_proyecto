import os
import shutil
import sys
from typing import Union, Optional

from .utils import detect_file_type, detect_encoding
from .permissions import FilePermissions, set_file_permissions, get_file_permissions
from .metadata import FileMetadata, get_metadata, set_file_times
from .links import (
    create_hard_link, 
    create_symbolic_link, 
    create_junction, 
    read_link, 
    is_junction, 
    is_symlink
)

class FSManager:
    _log_callback = None

    @classmethod
    def set_log_callback(cls, callback):
        cls._log_callback = callback

    @classmethod
    def _log(cls, cmd: str, syscall: str):
        if cls._log_callback:
            # Enviar directamente el comando y la syscall sin prefijos internos
            cls._log_callback(f"{cmd} | Syscall: {syscall}")

    @classmethod
    def get_metadata(cls, path: str, silent: bool = False) -> FileMetadata:
        """
        Retrieves complete metadata for the given path.
        
        Syscall: newfstatat(2)
        Comando: stat <path>
        """
        if not silent:
            cls._log(f"stat {path}", "newfstatat(2)")
        return get_metadata(path)

    @classmethod
    def set_permissions(cls, path: str, permissions: Union[FilePermissions, int, str]) -> None:
        """
        Sets permissions on a file or directory.
        
        Syscall: fchmodat(2)
        Comando: chmod <perms> <path>
        """
        cls._log(f"chmod {permissions} {path}", "fchmodat(2)")
        set_file_permissions(path, permissions)

    @classmethod
    def set_times(
        cls, 
        path: str, 
        atime: Optional[float] = None, 
        mtime: Optional[float] = None, 
        birthtime: Optional[float] = None
    ) -> None:
        """
        Sets access (atime), modification (mtime), and creation (birthtime) timestamps.
        
        Syscall: utimensat(2)
        Comando: touch -a -m -t <time> <path>
        """
        cls._log(f"touch {path}", "utimensat(2)")
        set_file_times(path, atime, mtime, birthtime)

    @classmethod
    def create_link(cls, link_type: str, src: str, dst: str) -> None:
        """
        Creates a link.
        
        Syscall: linkat(2) / symlinkat(2)
        Comando: ln <src> <dst>
        """
        link_type = link_type.lower()
        if link_type == 'hard':
            cls._log(f"ln {src} {dst}", "linkat(2)")
            create_hard_link(src, dst)
        elif link_type in ('symlink', 'sym'):
            cls._log(f"ln -s {src} {dst}", "symlinkat(2)")
            create_symbolic_link(src, dst)
        elif link_type == 'junction':
            cls._log(f"mklink /J {dst} {src}", "NTFS Junction")
            create_junction(src, dst)
        else:
            raise ValueError(f"Unknown link type: {link_type}.")

    @classmethod
    def read_file(cls, path: str) -> Union[str, bytes]:
        """
        Reads file content.
        
        Syscall: openat(2) + read(2)
        Comando: cat <path>
        """
        cls._log(f"cat {path}", "openat(2) + read(2)")
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
            
        ftype = detect_file_type(path)
        if ftype in ('binary', 'pdf', 'document'):
            with open(path, 'rb') as f:
                return f.read()
        else:
            encoding = detect_encoding(path)
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                return f.read()

    @classmethod
    def write_file(cls, path: str, content: Union[str, bytes], encoding: Optional[str] = None) -> None:
        """
        Writes content to a file.
        
        Syscall: openat(2) + write(2)
        Comando: echo <content> > <path>
        """
        cls._log(f"echo ... > {path}", "openat(2) + write(2)")
        if isinstance(content, bytes):
            with open(path, 'wb') as f:
                f.write(content)
        else:
            if encoding is None:
                if os.path.exists(path):
                    encoding = detect_encoding(path)
                else:
                    encoding = 'utf-8'
            write_encoding = 'utf-8' if (encoding == 'utf-8-sig' and os.path.exists(path)) else encoding
            with open(path, 'w', encoding=write_encoding, errors='replace') as f:
                f.write(content)

    @classmethod
    def touch(cls, path: str) -> None:
        """
        Creates an empty file if it doesn't exist.
        
        Syscall: openat(2) + utimensat(2)
        Comando: touch <path>
        """
        if os.path.exists(path):
            cls._log(f"touch {path}", "utimensat(2)")
            os.utime(path, None)
        else:
            cls._log(f"touch {path}", "openat(2) + utimensat(2)")
            with open(path, 'w', encoding='utf-8') as f:
                pass

    @classmethod
    def mkdir(cls, path: str, recursive: bool = True) -> None:
        """
        Creates a directory.
        
        Syscall: mkdirat(2)
        Comando: mkdir -p <path>
        """
        cls._log(f"mkdir {'-p' if recursive else ''} {path}", "mkdirat(2)")
        if recursive:
            os.makedirs(path, exist_ok=True)
        else:
            os.mkdir(path)

    @classmethod
    def delete(cls, path: str) -> None:
        """
        Deletes a file or directory.
        
        Syscall: unlinkat(2) / rmdir(2)
        Comando: rm -rf <path>
        """
        if not os.path.exists(path) and not os.path.islink(path):
            raise FileNotFoundError(f"Path not found: {path}")

        if is_junction(path) or os.path.islink(path):
            cls._log(f"rm {path}", "unlinkat(2)")
            if sys.platform == 'win32' and os.path.isdir(path):
                os.rmdir(path)
            else:
                os.unlink(path)
        elif os.path.isdir(path):
            cls._log(f"rm -rf {path}", "unlinkat(2) + rmdir(2)")
            cls._delete_tree_custom(path)
        else:
            cls._log(f"rm {path}", "unlinkat(2)")
            os.unlink(path)

    @classmethod
    def load_directory_ls(cls, path: str) -> str:
        """
        Simulates 'ls -la' output.
        
        Syscall: getdents64(2) + newfstatat(2)
        Comando: ls -la <path>
        """
        # Note: We don't log here because gui.py handles the full shell simulation log
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Not a directory: {path}")

        import datetime
        import pwd
        import grp
        import stat as stat_mod

        lines = []
        try:
            items = ['.', '..'] + sorted(os.listdir(path))
        except PermissionError:
            return "ls: permission denied"
        
        for item in items:
            p = os.path.join(path, item)
            try:
                st = os.lstat(p)
                
                # POSIX mode string
                is_dir = 'd' if os.path.isdir(p) else '-'
                if os.path.islink(p): is_dir = 'l'
                
                mode = stat_mod.S_IMODE(st.st_mode)
                perms = FilePermissions.from_octal(mode).to_symbolic()
                mode_str = is_dir + perms

                try:
                    user = pwd.getpwuid(st.st_uid).pw_name
                    group = grp.getgrgid(st.st_gid).gr_name
                except (KeyError, ImportError):
                    user = str(st.st_uid)
                    group = str(st.st_gid)

                # Format size like ls -lh
                def fmt_size(b):
                    for u in ['B','K','M','G']:
                        if b < 1024: return f"{b}{u}" if u=='B' else f"{b:.1f}{u}"
                        b /= 1024
                    return f"{b:.1f}T"
                
                size = fmt_size(st.st_size)
                mtime = datetime.datetime.fromtimestamp(st.st_mtime)
                time_str = mtime.strftime("%b %d %H:%M")

                icon = "" if os.path.isdir(p) else ""
                if os.path.islink(p): icon = "🔗"
                
                name = item
                if os.path.islink(p):
                    try:
                        target = os.readlink(p)
                        name = f"{item} -> {target}"
                    except OSError: pass

                lines.append(f"{mode_str} {user} {group} {size:>6} {time_str} {icon} {name}")
            except Exception: continue

        return "\n".join(lines)

    @classmethod
    def copy(cls, src: str, dst: str) -> None:
        """
        Copies a file or directory.
        
        Syscall: openat(2) + read(2) + write(2)
        Comando: cp -rp <src> <dst>
        """
        cls._log(f"cp -rp {src} {dst}", "openat(2) + read(2) + write(2)")
        if not os.path.exists(src) and not os.path.islink(src):
            raise FileNotFoundError(f"Source path not found: {src}")

        if is_junction(src):
            target = read_link(src)
            create_junction(target, dst)
        elif is_symlink(src):
            target = read_link(src)
            create_symbolic_link(target, dst, is_dir=os.path.isdir(src))
        elif os.path.isdir(src):
            cls._copy_tree_custom(src, dst)
        else:
            shutil.copy2(src, dst)

    @classmethod
    def move(cls, src: str, dst: str) -> None:
        """
        Moves (renames) a file or directory.
        
        Syscall: renameat2(2)
        Comando: mv <src> <dst>
        """
        cls._log(f"mv {src} {dst}", "renameat2(2)")
        if not os.path.exists(src) and not os.path.islink(src):
            raise FileNotFoundError(f"Source path not found: {src}")
        shutil.move(src, dst)
