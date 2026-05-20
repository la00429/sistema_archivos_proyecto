# PyFSManager — Manual de Programador

Este manual está dirigido a desarrolladores que contribuyen al proyecto.

## Estructura del proyecto

- `pyfsmanager/` — paquete principal con módulos: `cli.py`, `gui.py`, `manager.py`, `links.py`, `metadata.py`, `permissions.py`, `utils.py`.
- `tests/` — pruebas unitarias.
- `requirements.txt`, `setup.py`, `README.md`.

## Ejecutar y probar localmente

Instala dependencias y el paquete en editable:

```bash
python -m venv venv
source venv/bin/activate  # o venv\Scripts\Activate.ps1 en Windows
python -m pip install -r requirements.txt
python -m pip install -e .
```

Ejecutar tests:

```bash
python -m pytest -q
```

## Convenciones de código
- Estilo: seguir PEP8/flake8 si está configurado.
- Tipado: añade hints de tipo donde sea útil.
- Tests: cada nueva funcionalidad requiere tests que cubran casos positivos y negativos.

## Desarrollo de la CLI

Los comandos están en `pyfsmanager/cli.py`. Observaciones:
- Varias funciones contienen `pass` como placeholder; implementa la lógica allí y añade tests en `tests/test_manager.py` o crear tests específicos para comandos.

## Desarrollo de la GUI

- Archivo principal: `pyfsmanager/gui.py`.
- Características nuevas implementadas: búsqueda/filtrado en el árbol de archivos, menú contextual (clic derecho) con acciones comunes y atajos de teclado para operaciones frecuentes. Estas funcionalidades están implementadas de forma que reutilicen los métodos existentes en `FSManager`.
- Atajos implementados: `Ctrl+R` (recargar), `Ctrl+N` (nuevo archivo), `Ctrl+Shift+N` (nueva carpeta), `Ctrl+F` (foco en búsqueda).

Para añadir o cambiar acciones del menú contextual, modifica `on_tree_right_click` en `pyfsmanager/gui.py`.

## Permisos y metadatos

- `pyfsmanager/permissions.py` implementa la abstracción de permisos cross-platform. Hay ramas con `pass` que requieren implementación (NTFS ACL vs POSIX mapping). Ver los tests en `tests/test_permissions.py` para la API esperada.
- `pyfsmanager/metadata.py` gestiona `atime`, `mtime`, `birthtime`; revisar `pass` en ese archivo.

## Enlaces (links)
- `pyfsmanager/links.py` debe exponer: `create_hard_link`, `create_symbolic_link`, `create_junction`, `read_link`, `is_junction`, `is_symlink`.
- Implementa y testea el comportamiento en Windows y Unix. Usa `os.link`, `os.symlink` y `ctypes` o `pywin32` para junctions en Windows según disponibilidad.

## GUI

- `pyfsmanager/gui.py` contiene stubs; la GUI puede estar basada en `tkinter`, `PyQt` o `Tk`. Decide la dependencia y documenta instalación. Añade tests de integración manual para la GUI y pequeños smoke tests automatizables.

## Integración continua y empaquetado

- `setup.py` define `console_scripts` para `pyfs` y `pyfs-gui`. Asegúrate de que `entry_points` apunten a funciones `main()` exportadas.

## Lista de implementaciones prioritarias (placeholders detectados)
- `pyfsmanager/cli.py` — varios comandos con `pass`. ([cli.py](pyfsmanager/cli.py))
- `pyfsmanager/permissions.py` — ramas sin implementar. ([permissions.py](pyfsmanager/permissions.py))
- `pyfsmanager/links.py` — operaciones de enlace incompletas. ([links.py](pyfsmanager/links.py))
- `pyfsmanager/manager.py` — lógica principal con fallback `pass`. ([manager.py](pyfsmanager/manager.py))
- `pyfsmanager/gui.py` — stubs GUI. ([gui.py](pyfsmanager/gui.py))
- `pyfsmanager/metadata.py` — manejo de metadatos con `pass`. ([metadata.py](pyfsmanager/metadata.py))

## Checklist de pull request
- Añadir/actualizar tests.
- Ejecutar `python -m pytest` y asegurarse de que pase.
- Mantener cambios pequeños y dirigidos.
- Actualizar `documentation/` si el comportamiento público cambia.

---
Notas: Cuando implementes funciones que actualmente son `pass`, documenta la decisión de diseño en la sección correspondiente de este manual y añade tests que cubran la nueva lógica.
