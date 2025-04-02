class File:
    """File model class."""
    
    def __init__(self, path, content=None, file_hash=None):
        """Initialize a file model."""
        self.path = path
        self.content = content
        self.hash = file_hash
    
    def to_dict(self):
        """Convert file to a dictionary."""
        return {
            "path": self.path,
            "content": self.content,
            "hash": self.hash
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a file from a dictionary."""
        return cls(
            data["path"],
            data.get("content"),
            data.get("hash")
        )