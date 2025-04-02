import os
import re

def sanitize_path(path):
    """Sanitize a path to prevent directory traversal attacks."""
    path = re.sub(r'[^\w\s\-.]', '', path)
    path = path.strip()
    return path

def ensure_dir_exists(path):
    """Ensure a directory exists, creating it if necessary."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    return path

def join_path(*args):
    """Join path components safely."""
    return os.path.join(*[sanitize_path(arg) for arg in args])