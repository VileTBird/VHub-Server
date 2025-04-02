from flask import jsonify
from abc import ABC, abstractmethod

class BaseVCSImplementation(ABC):
    """Base class for VCS implementations."""
    
    @abstractmethod
    def create_repo(self, data):
        """Create a new repository."""
        pass
    
    @abstractmethod
    def list_repos(self):
        """List all repositories."""
        pass
    
    @abstractmethod
    def get_commits(self, repo_name):
        """Get all commits for a repository."""
        pass
    
    @abstractmethod
    def get_commit(self, repo_name, commit_id):
        """Get details of a specific commit."""
        pass
    
    @abstractmethod
    def check_commit(self, repo_name, commit_id):
        """Check if a commit exists in the repository."""
        pass
    
    @abstractmethod
    def push_commit(self, data):
        """Push a commit to a repository."""
        pass
    
    @abstractmethod
    def delete_repo(self, repo_name):
        """Delete a repository."""
        pass
    
    def validate_repo_name(self, repo_name):
        """Validate a repository name."""
        if not repo_name or '/' in repo_name or '\\' in repo_name:
            return False
        return True