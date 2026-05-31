import os

def detect_file_type(path: str) -> str:
    """
    Determines if a file is 'text', 'binary', 'pdf', 'document', or 'unknown' (e.g. if it doesn't exist or is a directory).
    """
    if not os.path.exists(path) or os.path.isdir(path):
        return 'unknown'
        
    try:
        with open(path, 'rb') as f:
            chunk = f.read(4096)
    except Exception:
        return 'unknown'

    lower_path = path.lower()
    if lower_path.endswith('.pdf') or chunk.startswith(b'%PDF-'):
        return 'pdf'

    if lower_path.endswith(('.doc', '.docx', '.rtf', '.odt', '.xls', '.xlsx', '.ppt', '.pptx')):
        return 'document'
        
    # An empty file is considered text by default
    if not chunk:
        return 'text'
        
    # Check for null byte
    if b'\x00' in chunk:
        return 'binary'
        
    # Try to decode with standard encodings. If none work, we treat it as binary.
    encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'cp1252', 'latin-1']
    for enc in encodings:
        try:
            chunk.decode(enc)
            return 'text'
        except UnicodeDecodeError:
            continue
            
    return 'binary'

def detect_encoding(path: str) -> str:
    """
    Tries to detect the encoding of a text file. Returns the encoding name,
    or 'utf-8' as a fallback if it cannot be determined or if it's binary.
    """
    if not os.path.exists(path) or os.path.isdir(path):
        return 'utf-8'
        
    try:
        with open(path, 'rb') as f:
            chunk = f.read(4096)
    except Exception:
        return 'utf-8'
        
    if not chunk:
        return 'utf-8'
        
    encodings = ['utf-8', 'utf-8-sig', 'utf-16', 'cp1252', 'latin-1']
    for enc in encodings:
        try:
            chunk.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
            
    return 'utf-8'
