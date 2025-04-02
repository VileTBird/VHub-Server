import hashlib
import zlib
import base64

def calculate_hash(content):
    """Calculate a SHA-1 hash of content."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha1(content).hexdigest()

def compress_content(content):
    """Compress content using zlib."""
    if isinstance(content, str):
        content = content.encode('utf-8')
    compressed = zlib.compress(content)
    return base64.b64encode(compressed).decode('utf-8')

def decompress_content(compressed_content):
    """Decompress content using zlib."""
    if isinstance(compressed_content, str):
        compressed_content = compressed_content.encode('utf-8')
    decompressed = zlib.decompress(base64.b64decode(compressed_content))
    return decompressed.decode('utf-8')