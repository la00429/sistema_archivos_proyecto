# PyFSManager — Manual de Usuario

Este documento explica cómo instalar y usar PyFSManager desde la perspectiva de un usuario final.

## Requisitos
- Python 3.9+
- Dependencias: ver `requirements.txt`.

## Instalación rápida
1. Clona el repositorio.
2. Crea y activa un entorno virtual.

```bash
python -m venv venv
# Windows PowerShell
venv\Scripts\Activate.ps1
# Linux / macOS
source venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
```

## Ejecutar la CLI

Inicia la interfaz de línea de comandos:

```bash
python -m pyfsmanager.cli
# o, si instalaste los entry points
pyfs
```

Comandos principales (resumen):
- `pwd`: muestra el directorio actual.
- `cd <ruta>`: cambia directorio.
- `ls [ruta]`: lista contenidos.
- `stat <ruta>`: muestra metadatos.
- `chmod <ruta> <modo>`: cambia permisos (octal/simbólico/relativo).
- `touch <ruta>`: crea/actualiza timestamps.
- `mkdir <ruta>`: crea directorios recursivos.
- `rm <ruta>`: elimina (pide confirmación).
- `cp <origen> <destino>`: copia (recursiva cuando aplica).
- `mv <origen> <destino>`: mueve/renombra.
- `link <hard|sym|junction> <nombre> <destino>`: crea enlaces.
- `cat <ruta>`: muestra contenido (hexdump si es binario).

### Ejemplos rápidos

Listar y ver metadatos:
```bash
pyfs
ls .
stat README.md
```

Crear un enlace simbólico (Unix/Windows con privilegios o Developer Mode):
```bash
link sym mi_enlace README.md
```

## Interfaz gráfica (GUI)

Arrancar GUI:

```bash
python -m pyfsmanager.gui
# o
pyfs-gui
```

La GUI permite explorar carpetas, ver/editar metadatos, cambiar permisos visualmente, ver hex dump de archivos binarios y realizar operaciones comunes (copiar, mover, borrar, crear enlaces).

## Solución de problemas comunes
- Si faltan permisos para crear symlinks en Windows, activa Developer Mode o ejecuta con privilegios.
- Si la GUI no se inicia, revisa dependencias y ejecuta `python -m pytest` para comprobar integridad básica.

## Soporte y contribuciones
- Abrir *issues* en el repositorio para errores o mejoras.
- Antes de enviar PR, asegúrate de que `python -m pytest` pase.

---
Licencia: MIT
