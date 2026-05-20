# Tickets / Issues sugeridos

1. **Implementar handlers de CLI faltantes**
   - Archivos: [pyfsmanager/cli.py](pyfsmanager/cli.py)
   - Descripción: Hay múltiples funciones/ramas con `pass` que representan comandos no implementados. Implementar cada comando según la especificación en `README.md` y añadir tests.
   - Prioridad: Alta
   - Estimación: 3–6h

2. **Completar abstracción de permisos cross-platform**
   - Archivos: [pyfsmanager/permissions.py](pyfsmanager/permissions.py), [tests/test_permissions.py](tests/test_permissions.py)
   - Descripción: Implementar mapping POSIX <-> NTFS ACL, manejo de errores y pruebas de compatibilidad.
   - Prioridad: Alta
   - Estimación: 4–8h

3. **Implementar operaciones de enlaces**
   - Archivos: [pyfsmanager/links.py](pyfsmanager/links.py), [tests/test_links.py](tests/test_links.py)
   - Descripción: Implementar `create_hard_link`, `create_symbolic_link`, `create_junction`, `read_link`, `is_junction`, `is_symlink` y añadir pruebas en ambos OS.
   - Prioridad: Media
   - Estimación: 3–6h

4. **Completar manejo de metadatos**
   - Archivos: [pyfsmanager/metadata.py](pyfsmanager/metadata.py), [tests/test_metadata.py](tests/test_metadata.py)
   - Descripción: Implementar lectura/escritura de `atime`, `mtime`, `birthtime` y añadir pruebas.
   - Prioridad: Media
   - Estimación: 2–4h

5. **Finalizar GUI y documentar dependencias**
   - Archivos: [pyfsmanager/gui.py](pyfsmanager/gui.py), `documentation/DEVELOPER_MANUAL.md`
   - Descripción: Completar componentes principales de la GUI, documentar la librería usada y crear pruebas de smoke.
   - Prioridad: Baja
   - Estimación: 6–12h

6. **Revisión de `pass` restantes y limpieza**
   - Archivos: todo el paquete `pyfsmanager/`
   - Descripción: Revisar todas las apariciones de `pass` y convertir en implementaciones, logs o `# TODO` con ticket referenciado.
   - Prioridad: Media
   - Estimación: 2–4h

---
Para asignar o comenzar, crea una rama por ticket `feature/<ticket>-descripcion` y abre un PR con tests y un pequeño changelog.
