# PyFSManager - Manejador de Sistemas de Archivos Multiplataforma

Gestor de sistemas de archivos en Python con detección automática de plataforma (Linux/Windows), abstracción de permisos, metadatos y operaciones de archivos de forma unificada.

## Características

- **Detección automática** del sistema operativo (Linux/Windows/macOS)
- **Abstracción de permisos**: modelo unificado sobre POSIX (rwx) y ACL (NTFS)
- **Gestión de enlaces**: hard links, symbolic links, junctions (Windows)
- **Metadatos cross-platform**: mtime, ctime, atime, birthtime
- **Soporte de tipos de archivo**: regular, directorio, symlink, FIFO, socket
- **Modo texto vs binario** con detección automática de codificación
- **CLI interactiva** y API programática

## Requisitos

- Python 3.9+
- Windows: Windows 10/11 o Server 2016+ (para symlinks sin admin)
- Linux: cualquier distribución con kernel 4.x+

## Instalación

```bash
# Clonar repositorio
git clone https://github.com/tuusuario/pyfsmanager.git
cd pyfsmanager

# Crear entorno virtual
python -m venv venv

# Activar (Linux/macOS)
source venv/bin/activate

# Activar (Windows PowerShell)
venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt

# Instalar en modo desarrollo
pip install -e .