# PyFSManager - Manejador de Sistemas de Archivos Multiplataforma

Gestor de sistemas de archivos en Python con detección automática de plataforma (Linux/Windows), abstracción de permisos, metadatos y operaciones de archivos de forma unificada.

## Características

- **Detección automática** del sistema operativo (Linux/Windows/macOS)
- **Abstracción de permisos**: modelo unificado sobre POSIX (rwx) y ACL (NTFS)
- **Gestión de enlaces**: hard links, symbolic links, junctions (Windows)
- **Metadatos cross-platform**: mtime, ctime, atime, birthtime (fecha de creación)
- **Soporte de tipos de archivo**: regular, directorio, symlink, FIFO, socket
- **Modo texto vs binario** con detección automática de codificación
- **CLI interactiva** coloreada y **GUI de escritorio** con temática oscura
- **API programática** clara y documentada

## Requisitos

- Python 3.9+
- Módulo `tkinter` para la GUI (suele venir con la instalación de Python en Windows/macOS; en Linux puede requerir un paquete adicional).
- En Windows, para aplicar cambios avanzados de permisos se recomienda instalar `pywin32` (opcional); si no está disponible se usan utilidades nativas (`icacls`) en modo "best-effort".

Notas por plataforma:

- Windows: Windows 10/11 o Server 2016+. Para crear symlinks sin privilegios puedes habilitar el modo desarrollador (Settings → For developers) o ejecutar el shell con permisos elevados. Las junctions (mklink /J) se usan como alternativa donde aplique.
- Linux/macOS: cualquier distribución moderna con Python 3.9+ y soporte estándar de POSIX.

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

# Activar (Windows CMD)
venv\Scripts\activate.bat

# Instalar dependencias y paquete en modo desarrollo
python -m pip install -r requirements.txt
python -m pip install -e .

# (Opcional) En Windows, instalar pywin32 para mejor manejo de ACLs
python -m pip install pywin32

# Nota: si no deseas instalar el paquete en modo editable, puedes
# ejecutar las interfaces usando el flag -m (ver secciones siguientes).
```

## Uso de la Interfaz de Línea de Comandos (CLI)

PyFSManager incluye una interfaz interactiva tipo shell con autocompletado, colores y formato claro de salida.

Para iniciarla, ejecuta (desde el entorno virtual o instalando el paquete):

Usando el módulo:
```bash

python -m pyfsmanager.cli
```
Si instalaste el paquete en modo editable o desde PyPI, también está disponible el entrypoint:
```bash
pyfs
```

### Comandos Disponibles

| Comando | Sintaxis | Descripción |
| :--- | :--- | :--- |
| **pwd** | `pwd` | Muestra el directorio de trabajo actual. |
| **cd** | `cd <ruta>` | Cambia el directorio de trabajo actual. |
| **ls** | `ls [ruta]` | Lista el contenido del directorio en formato tabular coloreado. |
| **stat** | `stat <ruta>` | Muestra metadatos detallados del archivo o carpeta. |
| **chmod** | `chmod <ruta> <modo>` | Cambia los permisos. Acepta octal (ej. `755`), simbólico (`rwxr-xr-x`) o relativo (`u+w,g-r`). |
| **touch** | `touch <ruta>` | Crea un archivo vacío o actualiza su fecha de acceso/modificación. |
| **mkdir** | `mkdir <ruta>` | Crea un directorio y sus carpetas padres si no existen. |
| **rm** | `rm <ruta>` | Elimina un archivo, directorio o enlace simbólico (pide confirmación). |
| **cp** | `cp <origen> <destino>` | Copia un archivo o directorio de forma recursiva. |
| **mv** | `mv <origen> <destino>` | Mueve o renombra un archivo o directorio. |
| **link** | `link <hard\|sym\|junction> <nombre> <destino>` | Crea un enlace duro, simbólico o de unión (Junction en Windows). |
| **cat** | `cat <ruta>` | Muestra el contenido. Si detecta que es binario, realiza un volcado hexadecimal (hexdump). |
| **exit** | `exit` | Sale del CLI interactivo. |

---

## Uso de la Interfaz Gráfica (GUI)

La interfaz gráfica ofrece un diseño oscuro moderno para gestionar visualmente tus archivos.

Para iniciarla, ejecuta (desde el entorno virtual o paquete instalado):

Usando el módulo:
```bash
python -m pyfsmanager.gui
```
O mediante el entrypoint si instalaste el paquete:
```bash
pyfs-gui
```

### Características de la GUI
- **Explorador Visual**: Navega por carpetas haciendo doble clic y utiliza el panel lateral con accesos rápidos.
- **Detalles y Tiempos**: Muestra el tamaño del archivo, tipo de objeto y fechas completas. Permite modificar las marcas de tiempo (`atime`, `mtime`, `birthtime`) mediante un diálogo gráfico.
- **Edición de Permisos**: Modifica de forma visual e interactiva los bits rwx mediante Checkboxes para Usuario, Grupo y Otros, aplicando los cambios directamente a la seguridad del sistema de archivos.
- **Editor de Texto Integrado**: Permite leer y editar archivos de texto con autodetección de encoding.
- **Visor Hexadecimal**: Visualiza archivos binarios mediante un volcado hexadecimal embebido de solo lectura.
- **Gestión de Enlaces y Operaciones**: Copia, mueve, renombra, elimina o crea enlaces visualmente mediante la barra de acciones.

---

## Pruebas Unitarias

Para validar que la suite de pruebas unitarias funcione correctamente en tu entorno actual:

```bash
# Ejecutar todas las pruebas con pytest
python -m pytest
```

Las pruebas cubren:
- Normalización y conversión de permisos.
- Lectura y escritura de marcas de tiempo detalladas.
- Creación, lectura y detección de enlaces simbólicos, duros y junctions.
- Operaciones CRUD (creación, lectura, copia, movimiento, eliminación) e inferencia de codificación y tipo.

---

## Contribución

Las contribuciones son bienvenidas. Para comenzar:
1. Forkea el repositorio.
2. Crea una rama para tu característica o corrección (`git checkout -b feature/nueva-funcionalidad`).
3. Asegúrate de que todas las pruebas pasen (`python -m pytest`).
4. Envía un Pull Request describiendo los cambios y la motivación.

## Licencia

Este proyecto está bajo la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

## Contacto

Si tienes preguntas, problemas o sugerencias, abre un *issue* en GitHub o contacta al mantenedor en `mailto:maintainer@example.com`.