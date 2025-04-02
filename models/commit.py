import datetime

class Commit:
    """Commit model class."""
    
    def __init__(self, commit_id, message, author, timestamp=None, parent_id=None):
        """Initialize a commit model."""
        self.id = commit_id
        self.message = message
        self.author = author
        self.timestamp = timestamp or datetime.datetime.now().isoformat()
        self.parent_id = parent_id
        self.files = {}
    
    def add_file(self, file_path, file_hash, content):
        """Add a file to the commit."""
        self.files[file_path] = {
            "hash": file_hash,
            "content": content
        }
    
    def to_dict(self):
        """Convert commit to a dictionary."""
        return {
            "id": self.id,
            "message": self.message,
            "author": self.author,
            "timestamp": self.timestamp,
            "parent_id": self.parent_id,
            "files": self.files
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a commit from a dictionary."""
        commit = cls(
            data["id"],
            data["message"],
            data["author"],
            data.get("timestamp"),
            data.get("parent_id")
        )
        commit.files = data.get("files", {})
        return commit