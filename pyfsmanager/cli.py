import os
import sys
import cmd
import shlex
import traceback
import time
from typing import List

import colorama
from colorama import Fore, Style

from .manager import FSManager
from .metadata import FileMetadata
from .permissions import FilePermissions
from .utils import detect_file_type, detect_encoding

# Initialize colorama
colorama.init(autoreset=True)

BANNER = r"""
  _____        ______  _____ __  __                                   
 |  __ \      |  ____|/ ____|  \/  |                                  
 | |__) |   _ | |__  | (___ | \  / | __ _ _ __   __ _  __ _  ___ _ __ 
 |  ___/ | | |  __|   \___ \| |\/| |/ _` | '_ \ / _` |/ _` |/ _ \ '__|
 | |   | |_| | |      ____) | |  | | (_| | | | | (_| | (_| |  __/ |   
 |_|    \__, |_|     |_____/|_|  |_|\__,_|_| |_|\__,_|\__, |\___|_|   
         __/ |                                         __/ |          
        |___/                                         |___/           
"""

def format_size(bytes_size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024:
            return f"{bytes_size:.1f} {unit}" if unit != 'B' else f"{bytes_size} B"
        bytes_size /= 1024
    return f"{bytes_size:.1f} PB"

def format_time(ts: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

def hex_dump(data: bytes, max_bytes: int = 2048) -> str:
    lines = []
    limit = min(len(data), max_bytes)
    for i in range(0, limit, 16):
        chunk = data[i:i+16]
        hex_part1 = " ".join(f"{b:02x}" for b in chunk[:8])
        hex_part2 = " ".join(f"{b:02x}" for b in chunk[8:])
        hex_full = hex_part1 + ("  " if hex_part2 else "") + hex_part2
        hex_full = hex_full.ljust(49)
        
        ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
        lines.append(f"{i:08x}  {hex_full}  |{ascii_part}|")
        
    if len(data) > max_bytes:
        lines.append(f"... (truncado, total {len(data)} bytes) ...")
    return "\n".join(lines)


class PyFSCmd(cmd.Cmd):
    intro = Fore.CYAN + BANNER + Fore.YELLOW + "\nPyFSManager CLI interactivo. Escribe 'help' o '?' para ver los comandos.\n"
    
    def __init__(self):
        super().__init__()
        self.update_prompt()

    def update_prompt(self):
        cwd = os.getcwd()
        # Shorten path if it's too long
        if len(cwd) > 40:
            parts = cwd.split(os.sep)
            if len(parts) > 3:
                cwd = f"...{os.sep}{os.sep.join(parts[-2:])}"
        self.prompt = Fore.BLUE + "pyfs " + Fore.GREEN + f"[{cwd}]> " + Style.RESET_ALL

    def postcmd(self, stop, line):
        self.update_prompt()
        return stop

    def _parse_args(self, arg_str: str, min_args: int, max_args: int = None) -> List[str]:
        try:
            args = shlex.split(arg_str)
        except ValueError as e:
            print(Fore.RED + f"Error al parsear argumentos: {e}")
            raise
        if len(args) < min_args:
            print(Fore.RED + f"Error: Faltan argumentos. Se esperaban mínimo {min_args}, se obtuvieron {len(args)}.")
            raise ValueError()
        if max_args is not None and len(args) > max_args:
            print(Fore.RED + f"Error: Demasiados argumentos. Se esperaban máximo {max_args}, se obtuvieron {len(args)}.")
            raise ValueError()
        return args

    # --- Commands ---

    def do_pwd(self, arg):
        """Muestra el directorio de trabajo actual.
Uso: pwd"""
        print(os.getcwd())

    def do_cd(self, arg):
        """Cambia el directorio de trabajo actual.
Uso: cd <ruta>"""
        try:
            args = self._parse_args(arg, 1, 1)
            os.chdir(args[0])
        except ValueError:
            pass
        except OSError as e:
            print(Fore.RED + f"Error: No se pudo cambiar al directorio: {e.strerror}")

    def do_ls(self, arg):
        """Lista archivos y carpetas en un directorio.
Uso: ls [ruta]"""
        try:
            args = self._parse_args(arg, 0, 1)
            target_dir = args[0] if args else "."
            
            if not os.path.exists(target_dir):
                print(Fore.RED + f"Error: El directorio no existe: {target_dir}")
                return
            if not os.path.isdir(target_dir):
                print(Fore.RED + f"Error: La ruta no es un directorio: {target_dir}")
                return

            items = os.listdir(target_dir)
            
            # Sort items: directories first, then links, then files, alphabetically
            item_metas = []
            for item in items:
                p = os.path.join(target_dir, item)
                try:
                    meta = FSManager.get_metadata(p)
                    item_metas.append(meta)
                except Exception:
                    # If we can't read metadata, skip or create dummy
                    pass
            
            def sort_key(meta: FileMetadata):
                type_order = {'directory': 0, 'junction': 1, 'symlink': 2, 'fifo': 3, 'socket': 4, 'regular': 5, 'unknown': 6}
                return (type_order.get(meta.type, 9), meta.name.lower())

            item_metas.sort(key=sort_key)

            # Print header
            print(f"{'TIPO':<10} {'PERMISOS':<10} {'LINKS':<6} {'TAMAÑO':<10} {'MODIFICADO':<20} {'NOMBRE'}")
            print("-" * 85)
            
            for meta in item_metas:
                type_str = meta.type.upper()
                perms_str = meta.permissions.to_symbolic()
                size_str = format_size(meta.size) if meta.type == 'regular' else '-'
                time_str = format_time(meta.mtime)
                
                # Apply colors based on type, truncate long names to keep columns aligned
                MAX_NAME = 40
                if meta.type == 'directory':
                    display_name = Fore.BLUE + meta.name[:MAX_NAME] + Style.RESET_ALL
                elif meta.type == 'junction':
                    display_name = Fore.CYAN + meta.name[:MAX_NAME] + Style.RESET_ALL
                elif meta.type == 'symlink':
                    display_name = Fore.CYAN + meta.name[:MAX_NAME] + Style.RESET_ALL
                elif 'x' in meta.permissions.user and meta.type == 'regular':
                    display_name = Fore.GREEN + meta.name[:MAX_NAME] + Style.RESET_ALL
                else:
                    display_name = meta.name[:MAX_NAME]

                print(f"{type_str:<10} {perms_str:<10} {meta.nlink:<6} {size_str:<10} {time_str:<20} {display_name}")

                # Print link target on a second line so it never misaligns columns
                if meta.link_target and meta.type in ('symlink', 'junction'):
                    print(f"{'':10} {'':10} {'':6} {'':10} {'':20} {Fore.CYAN}  └→ {meta.link_target}{Style.RESET_ALL}")
                
        except ValueError:
            pass
        except OSError as e:
            print(Fore.RED + f"Error al listar: {e}")

    def do_stat(self, arg):
        """Muestra metadatos detallados de un archivo o directorio.
Uso: stat <ruta>"""
        try:
            args = self._parse_args(arg, 1, 1)
            meta = FSManager.get_metadata(args[0])
            
            print(Fore.YELLOW + f"Metadatos de: {meta.name}")
            print(f"  Ruta absoluta:   {meta.path}")
            print(f"  Tipo de archivo: {meta.type.upper()}")
            print(f"  Tamaño:          {meta.size} bytes ({format_size(meta.size)})")
            print(f"  Permisos:        {meta.permissions.to_symbolic()} ({oct(meta.permissions.to_octal())})")
            print(f"  Hard links:      {meta.nlink}")
            if meta.link_target:
                print(f"  Destino enlace:  {meta.link_target}")
            print(f"  Acceso (atime):  {format_time(meta.atime)}")
            print(f"  Modif. (mtime):  {format_time(meta.mtime)}")
            print(f"  Cambio (ctime):  {format_time(meta.ctime)}")
            if meta.birthtime:
                print(f"  Creado (birth):  {format_time(meta.birthtime)}")
            else:
                print(f"  Creado (birth):  N/D (No soportado)")
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error al obtener metadatos: {e}")

    def do_chmod(self, arg):
        """Cambia los permisos de un archivo o directorio.
Acepta octal (ej. 755), simbólico completo (ej. rwxr-xr-x) o expresión chmod (ej. u+w,g-r).
Uso: chmod <ruta> <modo>"""
        try:
            args = self._parse_args(arg, 2, 2)
            path, mode = args[0], args[1]
            
            FSManager.set_permissions(path, mode)
            new_perms = FSManager.get_metadata(path).permissions
            print(Fore.GREEN + f"Permisos de '{path}' actualizados a: {new_perms.to_symbolic()} ({oct(new_perms.to_octal())})")
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error al cambiar permisos: {e}")

    def do_touch(self, arg):
        """Crea un archivo vacío o actualiza la marca de tiempo de un archivo existente.
Uso: touch <ruta>"""
        try:
            args = self._parse_args(arg, 1, 1)
            FSManager.touch(args[0])
            print(Fore.GREEN + f"Archivo '{args[0]}' tocado correctamente.")
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error: {e}")

    def do_mkdir(self, arg):
        """Crea un directorio (y sus carpetas padres si es necesario).
Uso: mkdir <ruta>"""
        try:
            args = self._parse_args(arg, 1, 1)
            FSManager.mkdir(args[0])
            print(Fore.GREEN + f"Directorio '{args[0]}' creado correctamente.")
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error al crear directorio: {e}")

    def do_rm(self, arg):
        """Elimina un archivo, directorio, symlink o junction.
Uso: rm <ruta>"""
        try:
            args = self._parse_args(arg, 1, 1)
            path = args[0]
            if not os.path.exists(path) and not os.path.islink(path):
                print(Fore.RED + f"Error: Ruta no encontrada: {path}")
                return
                
            confirm = input(f"¿Estás seguro de que quieres eliminar '{path}'? (s/n): ").strip().lower()
            if confirm == 's':
                FSManager.delete(path)
                print(Fore.GREEN + f"'{path}' eliminado correctamente.")
            else:
                print("Operación cancelada.")
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error al eliminar: {e}")

    def do_cp(self, arg):
        """Copia un archivo o directorio. Preserva symlinks y junctions.
Uso: cp <origen> <destino>"""
        try:
            args = self._parse_args(arg, 2, 2)
            src, dst = args[0], args[1]
            FSManager.copy(src, dst)
            print(Fore.GREEN + f"Copiado correctamente de '{src}' a '{dst}'.")
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error al copiar: {e}")

    def do_mv(self, arg):
        """Mueve o renombra un archivo o directorio.
Uso: mv <origen> <destino>"""
        try:
            args = self._parse_args(arg, 2, 2)
            src, dst = args[0], args[1]
            FSManager.move(src, dst)
            print(Fore.GREEN + f"Movido correctamente de '{src}' a '{dst}'.")
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error al mover/renombrar: {e}")

    def do_link(self, arg):
        """Crea un enlace (duro, simbólico o junction).
Uso: link <hard|sym|junction> <nombre_enlace> <destino>"""
        try:
            args = self._parse_args(arg, 3, 3)
            ltype, link_name, target = args[0], args[1], args[2]
            
            FSManager.create_link(ltype, target, link_name)
            print(Fore.GREEN + f"Enlace de tipo '{ltype}' creado en '{link_name}' apuntando a '{target}'.")
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error al crear enlace: {e}")

    def do_cat(self, arg):
        """Muestra el contenido de un archivo.
Si es texto, muestra el contenido descodificado automáticamente.
Si es binario, muestra un volcado hexadecimal.
Uso: cat <ruta>"""
        try:
            args = self._parse_args(arg, 1, 1)
            path = args[0]
            
            content = FSManager.read_file(path)
            ftype = detect_file_type(path)
            
            if ftype == 'pdf':
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(path)
                    print(Fore.YELLOW + f"--- PDF ({len(reader.pages)} páginas) ---")
                    for page in reader.pages[:3]:
                        page_text = page.extract_text() or "(sin texto extraíble)"
                        print(page_text)
                        print("\n--- Página ---\n")
                except Exception as e:
                    print(Fore.RED + f"No se pudo leer el PDF: {e}")
            elif ftype == 'binary':
                print(Fore.YELLOW + f"--- Contenido Binario (Hexdump) - {len(content)} bytes ---")
                print(hex_dump(content))
            else:
                encoding = detect_encoding(path)
                print(Fore.YELLOW + f"--- Contenido de Texto ({encoding.upper()}) - {len(content)} caracteres ---")
                print(content)
        except ValueError:
            pass
        except Exception as e:
            print(Fore.RED + f"Error al leer el archivo: {e}")

    def do_exit(self, arg):
        """Sale del CLI interactivo.
Uso: exit"""
        print("¡Adiós!")
        return True

    def do_EOF(self, arg):
        """Sale del CLI con Ctrl+D"""
        print()
        return self.do_exit(arg)


def main():
    try:
        PyFSCmd().cmdloop()
    except KeyboardInterrupt:
        print("\n¡Adiós!")
        sys.exit(0)

if __name__ == '__main__':
    main()
