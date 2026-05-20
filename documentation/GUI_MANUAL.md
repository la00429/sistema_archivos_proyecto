# PyFSManager — Manual de la GUI

Este documento describe cómo ejecutar y usar la interfaz gráfica de PyFSManager, además de notas para desarrolladores sobre la implementación actual basada en `tkinter`.

## Requisitos
- Python 3.9+
- `tkinter` (normalmente disponible con la instalación estándar de Python). En algunas distribuciones Linux requiere paquete extra (ej. `python3-tk`).
- En Windows, no hay dependencias adicionales; la GUI intenta activar DPI awareness si es posible.

## Ejecutar la GUI

Desde el paquete instalado o el entorno de desarrollo:

```bash
python -m pyfsmanager.gui
# o, si instalaste entry points
pyfs-gui
```

La aplicación abre una ventana principal con:
- Barra superior: navegación de rutas, botón de recarga y acceso directo para subir al parent.
- Panel central: lista de archivos con columna de nombre, tipo, tamaño y fecha de modificación.
- Panel derecho: detalles del elemento seleccionado (metadatos, permisos, acciones).
- Barra inferior: log de estado y mensajes.

## Funcionalidades implementadas
- Explorador de directorios con ordenación inteligente (directorios primero, luego enlaces, luego archivos).
- Editor de texto integrado con detección automática de codificación; visor hexadecimal para binarios.
- CRUD básico: crear archivo (`touch`), crear carpeta, copiar, mover, renombrar, eliminar.
- Gestión de permisos a nivel POSIX/ACL a través de `FilePermissions` y `FSManager.set_permissions`.
- Edición de marcas de tiempo (`atime`, `mtime`) y soporte de `birthtime` en Windows.
- Creación de enlaces: hard links, symlinks y junctions (Windows).
 - Búsqueda/filtrado rápido en la barra superior para encontrar archivos por nombre.
 - Menú contextual en la lista de archivos (clic derecho) con acciones: Abrir/Editar, Copiar, Mover, Renombrar, Eliminar y Crear Enlace.
 - Atajos de teclado: `Ctrl+R` (recargar), `Ctrl+N` (nuevo archivo), `Ctrl+Shift+N` (nueva carpeta), `Ctrl+F` (foco en búsqueda).

## Limitaciones y consideraciones
- La implementación usa `tkinter` para máxima compatibilidad; no hay dependencias externas de GUI.
- En Windows, operaciones sobre ACL requieren `pywin32` para funciones avanzadas; cuando no está disponible, el paquete intenta `icacls` como fallback.
- Crear symlinks en Windows puede requerir privilegios o Developer Mode.
- La GUI no está fuertemente testeada en entornos headless; evita ejecutar `main()` en CI sin display (usa pruebas unitarias que no inicien `mainloop`).

## Notas para desarrolladores
- Archivo principal: `pyfsmanager/gui.py`.
- La clase `PyFSApp` expone `load_directory(path)` para recargar una vista sin arrancar la interfaz.
- Para pruebas manuales: abrir Python REPL y hacer:

```py
from pyfsmanager.gui import PyFSApp
app = PyFSApp()
app.load_directory('.')
# Evita hacer `app.mainloop()` en entornos sin display
```

- Para añadir componentes, extiende `setup_ui()` y `setup_right_panel()`; reutiliza `FSManager` para operaciones de filesystem.

## Pruebas de smoke recomendadas
- Manual: abrir la GUI y crear/editar/un enlace en un directorio temporal.
- Automatizable (local): ejecutar pequeñas pruebas que no invoquen `mainloop`, p. ej. instanciar `PyFSApp` and llamar `load_directory` en un entorno con display.

## Nuevas notas de uso
- Para filtrar la vista, escribe en la caja de búsqueda (a la derecha de la barra de ruta). La lista se actualiza al teclear o pulsar Enter.
- Haz clic derecho sobre un elemento en la lista para ver acciones rápidas.

## Contribuciones
- Documenta cambios en `documentation/GUI_MANUAL.md` y añade pruebas donde sea posible.
# PyFSManager — Manual de la GUI

Este documento describe la interfaz gráfica incluida en PyFSManager, dependencias y pasos para pruebas manuales.

## Dependencias
- Python 3.9+ (incluye `tkinter` en la mayoría de las distribuciones oficiales).
- En Windows, para funcionalidades avanzadas (modificar birthtime, ACLs) es recomendable `pywin32`.

Nota: `tkinter` está incluido en la distribución estándar de CPython, pero en algunas distribuciones Linux se debe instalar el paquete del sistema (`python3-tk` o similar).

## Ejecutar la GUI

```bash
python -m pyfsmanager.gui
# o si instalaste el paquete
pyfs-gui
```

## Funcionalidades principales
- Explorador de archivos con lista central y panel de detalles.
- Editor integrado: edición de archivos de texto y visor hexadecimal para binarios.
- Gestión de enlaces: creación de enlaces duros, simbólicos y junctions (Windows).
- Edición de marcas de tiempo (`atime`, `mtime`, `birthtime` — este último sólo en Windows).
- Aplicación visual de permisos (checkboxes para user/group/other) que usa la abstracción de `permissions.py`.
- Operaciones CRUD: crear archivo/carpeta, copiar, mover, renombrar, eliminar.

## Uso rápido

- Navega a una carpeta usando la barra de direcciones o accesos rápidos en la barra lateral.
- Haz doble clic en un directorio para entrar; doble clic en un archivo para abrir el editor.
- Selecciona un elemento en la lista para ver metadatos y habilitar acciones a la derecha.

## Pruebas manuales (smoke)

1. Abrir la GUI.
2. Crear un archivo nuevo desde `Nuevo Archivo` -> comprobar que aparece y que `Editar` puede abrirlo.
3. Crear una carpeta desde `Nueva Carpeta` -> comprobar existencia.
4. Seleccionar un archivo y usar `Copiar`, `Mover` y `Renombrar` para verificar operaciones.
5. Probar `Crear Enlace` (nota: en Windows puede requerir privilegios/developer mode para symlinks).
6. Editar marcas de tiempo y comprobar los resultados con `stat` desde la CLI o `ls`.

## Ejecución headless / CI

La GUI no se debe ejecutar en entornos headless (CI) sin un servidor X virtual. Para pruebas automatizadas, crea pruebas unitarias para la lógica subyacente (métodos en `FSManager`, `links.py`, `permissions.py`, `metadata.py`) y evita instanciar `tk.Tk()` en CI.

## Solución de problemas
- Si la ventana no aparece en Linux, instala el paquete del sistema `python3-tk`.
- En Windows, si las operaciones de permisos o timestamps fallan, instala `pywin32`.
- Para problemas con symlinks en Windows, activa Developer Mode o ejecuta con privilegios elevados.

## Contribuciones

- Añadir pruebas de integración manual en `documentation/` describiendo cómo reproducir en cada plataforma.
- Si añades nuevas dependencias para la GUI (p. ej. PyQt), documenta cómo instalarlas y adapta `setup.py`.
