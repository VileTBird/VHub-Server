class Repository:
    """Repository model class."""
    
    def __init__(self, name, implementation=None):
        """Initialize a repository model."""
        self.name = name
        self.implementation = implementation
        self.commit_count = 0
        self.file_count = 0
        self.last_commit = None
    
    def to_dict(self):
        """Convert repository to a dictionary."""
        return {
            "name": self.name,
            "implementation": self.implementation,
            "commit_count": self.commit_count,
            "file_count": self.file_count,
            "last_commit": self.last_commit.to_dict() if self.last_commit else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a repository from a dictionary."""
        repo = cls(data["name"], data.get("implementation"))
        repo.commit_count = data.get("commit_count", 0)
        repo.file_count = data.get("file_count", 0)
        
        from models.commit import Commit
        if data.get("last_commit"):
            repo.last_commit = Commit.from_dict(data["last_commit"])
        
        return repo