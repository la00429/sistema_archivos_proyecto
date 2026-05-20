from .manager import FSManager
from .permissions import FilePermissions, get_file_permissions, set_file_permissions
from .metadata import FileMetadata, get_metadata, set_file_times
from .links import (
    create_hard_link, 
    create_symbolic_link, 
    create_junction, 
    read_link, 
    is_junction, 
    is_symlink
)
from .utils import detect_file_type, detect_encoding

__all__ = [
    'FSManager',
    'FilePermissions',
    'FileMetadata',
    'get_file_permissions',
    'set_file_permissions',
    'get_metadata',
    'set_file_times',
    'create_hard_link',
    'create_symbolic_link',
    'create_junction',
    'read_link',
    'is_junction',
    'is_symlink',
    'detect_file_type',
    'detect_encoding'
]
