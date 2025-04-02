import os
import json
import shutil
import datetime
import difflib
from flask import jsonify

from implementations.base import BaseVCSImplementation
from utils.path_utils import sanitize_path
from utils.hash_utils import calculate_hash

class GraphDatabaseImplementation(BaseVCSImplementation):
    """Object + Graph Database implementation"""
    
    def __init__(self):
        """Initialize the implementation."""
        self.base_dir = os.path.abspath("./repositories/graph_db")
        os.makedirs(self.base_dir, exist_ok=True)
    
    def get_repo_path(self, repo_name):
        """Get the path to a repository directory."""
        repo_dir = os.path.join(self.base_dir, sanitize_path(repo_name))
        return repo_dir
    
    def get_graph_db_path(self, repo_name):
        """Get the path to a repository's graph database."""
        repo_dir = self.get_repo_path(repo_name)
        return os.path.join(repo_dir, "graph.json")
    
    def get_objects_dir(self, repo_name):
        """Get the path to a repository's objects directory."""
        repo_dir = self.get_repo_path(repo_name)
        objects_dir = os.path.join(repo_dir, "objects")
        os.makedirs(objects_dir, exist_ok=True)
        return objects_dir
    
    def init_repo_graph(self, repo_name):
        """Initialize graph database for a repository."""
        graph_db_path = self.get_graph_db_path(repo_name)
        
        if not os.path.exists(graph_db_path):
            graph_data = {
                "commits": {},
                "changes": {}, 
                "branches": {
                    "main": None  
                },
                "HEAD": None
            }
            
            with open(graph_db_path, 'w') as f:
                json.dump(graph_data, f, indent=2)
    
    def create_repo(self, data):
        """Create a new repository."""
        if 'name' not in data:
            return jsonify({"error": "Repository name is required"}), 400
        
        repo_name = data['name']
        
        if not self.validate_repo_name(repo_name):
            return jsonify({"error": "Invalid repository name"}), 400
        
        repo_dir = self.get_repo_path(repo_name)
        
        if os.path.exists(repo_dir):
            return jsonify({"message": f"Repository '{repo_name}' already exists"}), 200
        
        os.makedirs(repo_dir, exist_ok=True)
        self.get_objects_dir(repo_name) 
        self.init_repo_graph(repo_name)
        
        return jsonify({"message": f"Repository '{repo_name}' created successfully"}), 200
    
    def list_repos(self):
        """List all repositories."""
        repos = []
        
        for repo_name in os.listdir(self.base_dir):
            repo_dir = os.path.join(self.base_dir, repo_name)  
            graph_db_path = os.path.join(repo_dir, "graph.json")  
            
            if os.path.isdir(repo_dir) and os.path.exists(graph_db_path):
                try:
                    with open(graph_db_path, 'r') as f:
                        graph_data = json.load(f)
                    
                    commit_count = len(graph_data.get("commits", {}))
                    
                    file_count = 0
                    for commit_id, commit_data in graph_data.get("commits", {}).items():
                        file_count += len(commit_data.get("files", {}))
                    
                    last_commit_info = None
                    head_commit_id = graph_data.get("HEAD")
                    if head_commit_id and head_commit_id in graph_data.get("commits", {}):
                        commit_data = graph_data["commits"][head_commit_id]
                        last_commit_info = {
                            "id": head_commit_id,
                            "message": commit_data.get("message"),
                            "author": commit_data.get("author"),
                            "timestamp": commit_data.get("timestamp")
                        }
                    
                    repos.append({
                        "name": repo_name,
                        "commit_count": commit_count,
                        "file_count": file_count,
                        "last_commit": last_commit_info
                    })
                except Exception as e:
                    print(f"Error getting stats for repository '{repo_name}': {e}")
        
        return jsonify(repos)
    
    def get_commits(self, repo_name):
        """Get all commits for a repository."""
        graph_db_path = self.get_graph_db_path(repo_name)
        
        if not os.path.exists(graph_db_path):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            with open(graph_db_path, 'r') as f:
                graph_data = json.load(f)
            
            commits = graph_data.get("commits", {})
            changes = graph_data.get("changes", {})
            
            result = []
            for commit_id, commit_data in commits.items():
                change_count = 0
                if commit_id in changes:
                    change_count = len(changes[commit_id])
                
                result.append({
                    "id": commit_id,
                    "message": commit_data.get("message"),
                    "author": commit_data.get("author"),
                    "timestamp": commit_data.get("timestamp"),
                    "parent_id": commit_data.get("parent_id"),
                    "change_count": change_count
                })
            
            result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return jsonify(result)
        
        except Exception as e:
            return jsonify({"error": f"Error getting commits: {e}"}), 500
    
    def get_object_content(self, repo_name, object_hash):
        """Get the content of an object from the object store."""
        objects_dir = self.get_objects_dir(repo_name)
        object_path = os.path.join(objects_dir, object_hash[:2], object_hash[2:])
        
        if os.path.exists(object_path):
            with open(object_path, 'r') as f:
                return f.read()
        
        return None
    
    def get_commit(self, repo_name, commit_id):
        """Get details of a specific commit with file changes."""
        graph_db_path = self.get_graph_db_path(repo_name)
        
        if not os.path.exists(graph_db_path):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            with open(graph_db_path, 'r') as f:
                graph_data = json.load(f)
            
            commits = graph_data.get("commits", {})
            changes = graph_data.get("changes", {})
            
            if commit_id not in commits:
                return jsonify({"error": f"Commit '{commit_id}' not found"}), 404
            
            commit_data = commits[commit_id]
            
            files_data = {}
            for file_path, file_hash in commit_data.get("files", {}).items():
                content = self.get_object_content(repo_name, file_hash)
                files_data[file_path] = {
                    "hash": file_hash,
                    "content": content
                }
            
            changes_data = {}
            if commit_id in changes:
                changes_data = changes[commit_id]
            
            result = {
                "id": commit_id,
                "message": commit_data.get("message"),
                "author": commit_data.get("author"),
                "timestamp": commit_data.get("timestamp"),
                "parent_id": commit_data.get("parent_id"),
                "files": files_data,
                "changes": changes_data
            }
            
            return jsonify(result)
        
        except Exception as e:
            return jsonify({"error": f"Error getting commit: {e}"}), 500
    
    def check_commit(self, repo_name, commit_id):
        """Check if a commit exists in the repository."""
        graph_db_path = self.get_graph_db_path(repo_name)
        
        if not os.path.exists(graph_db_path):
            return {"exists": False, "error": f"Repository '{repo_name}' not found"}, 404
        
        try:
            with open(graph_db_path, 'r') as f:
                graph_data = json.load(f)
            
            exists = commit_id in graph_data.get("commits", {})
            
            return {"exists": exists}, 200
        
        except Exception as e:
            return {"exists": False, "error": f"Error checking commit: {e}"}, 500
    
    def store_object(self, repo_name, content):
        """Store content in the object store and return its hash."""
        object_hash = calculate_hash(content)
        objects_dir = self.get_objects_dir(repo_name)
        
        subdir = os.path.join(objects_dir, object_hash[:2])
        os.makedirs(subdir, exist_ok=True)
        
        object_path = os.path.join(subdir, object_hash[2:])
        if not os.path.exists(object_path):
            with open(object_path, 'w') as f:
                f.write(content)
        
        return object_hash
    
    def calculate_changes(self, repo_name, commit_data):
        """Calculate changes between this commit and its parent."""
        graph_db_path = self.get_graph_db_path(repo_name)
        
        with open(graph_db_path, 'r') as f:
            graph_data = json.load(f)
        
        parent_id = commit_data.get('parent_id')
        changes = {}
        
        if not parent_id:
            for file_path, file_hash in commit_data['files'].items():
                changes[file_path] = {
                    "status": "added",
                    "diff": None,
                    "previous_hash": None,
                    "current_hash": file_hash
                }
        else:
            parent_files = {}
            if parent_id in graph_data.get("commits", {}):
                parent_commit = graph_data["commits"][parent_id]
                for file_path, file_hash in parent_commit.get("files", {}).items():
                    parent_content = self.get_object_content(repo_name, file_hash)
                    parent_files[file_path] = {
                        "hash": file_hash,
                        "content": parent_content
                    }
            
            current_files = {}
            for file_path, file_hash in commit_data['files'].items():
                current_content = self.get_object_content(repo_name, file_hash)
                current_files[file_path] = {
                    "hash": file_hash,
                    "content": current_content
                }
            
            all_paths = set(list(parent_files.keys()) + list(current_files.keys()))
            
            for file_path in all_paths:
                if file_path in current_files and file_path not in parent_files:
                    changes[file_path] = {
                        "status": "added",
                        "diff": None,
                        "previous_hash": None,
                        "current_hash": current_files[file_path]['hash']
                    }
                elif file_path not in current_files and file_path in parent_files:
                    # Deleted file
                    changes[file_path] = {
                        "status": "deleted",
                        "diff": None,
                        "previous_hash": parent_files[file_path]['hash'],
                        "current_hash": None
                    }
                elif current_files[file_path]['hash'] != parent_files[file_path]['hash']:
                    diff = '\n'.join(difflib.unified_diff(
                        parent_files[file_path]['content'].splitlines(),
                        current_files[file_path]['content'].splitlines(),
                        f'a/{file_path}',
                        f'b/{file_path}',
                        lineterm=''
                    ))
                    
                    changes[file_path] = {
                        "status": "modified",
                        "diff": diff,
                        "previous_hash": parent_files[file_path]['hash'],
                        "current_hash": current_files[file_path]['hash']
                    }
        
        return changes
    
    def push_commit(self, data):
        """Push a commit to a repository with change tracking."""
        if 'repo_name' not in data or 'id' not in data:
            return jsonify({"error": "Invalid commit data"}), 400
        
        repo_name = data['repo_name']
        
        if not self.validate_repo_name(repo_name):
            return jsonify({"error": "Invalid repository name"}), 400
        
        repo_dir = self.get_repo_path(repo_name)
        graph_db_path = self.get_graph_db_path(repo_name)
        
        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir, exist_ok=True)
            self.get_objects_dir(repo_name) 
            self.init_repo_graph(repo_name)
        
        try:
            with open(graph_db_path, 'r') as f:
                graph_data = json.load(f)
            
            if data['id'] in graph_data.get("commits", {}):
                return jsonify({"message": f"Commit '{data['id']}' already exists"}), 200
            
            files_hashes = {}
            for file_path, file_info in data.get('files', {}).items():
                content = file_info.get('content', '')
                file_hash = self.store_object(repo_name, content)
                files_hashes[file_path] = file_hash
            
            if "commits" not in graph_data:
                graph_data["commits"] = {}
            
            if "changes" not in graph_data:
                graph_data["changes"] = {}
            
            commit_data = {
                "message": data.get('message', ''),
                "author": data.get('author', ''),
                "timestamp": data.get('timestamp', datetime.datetime.now().isoformat()),
                "parent_id": data.get('parent_id'),
                "files": files_hashes
            }
            
            temp_commit_data = {
                "parent_id": data.get('parent_id'),
                "files": files_hashes
            }
            changes = self.calculate_changes(repo_name, temp_commit_data)
            
            graph_data["commits"][data['id']] = commit_data
            graph_data["changes"][data['id']] = changes
            
            current_head = graph_data.get("HEAD")
            if current_head is None or current_head == data.get('parent_id'):
                graph_data["HEAD"] = data['id']
                graph_data["branches"]["main"] = data['id']

            with open(graph_db_path, 'w') as f:
                json.dump(graph_data, f, indent=2)
            
            return jsonify({
                "message": f"Commit '{data['id']}' pushed successfully",
                "changes": len(changes)
            }), 200
        
        except Exception as e:
            return jsonify({"error": f"Error pushing commit: {e}"}), 500
    
    def get_changes(self, repo_name, commit_id):
        """Get changes made in a specific commit."""
        graph_db_path = self.get_graph_db_path(repo_name)
        
        if not os.path.exists(graph_db_path):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            with open(graph_db_path, 'r') as f:
                graph_data = json.load(f)
            
            if commit_id not in graph_data.get("commits", {}):
                return jsonify({"error": f"Commit '{commit_id}' not found"}), 404
            
            changes = graph_data.get("changes", {}).get(commit_id, {})
            
            return jsonify(changes)
        
        except Exception as e:
            return jsonify({"error": f"Error getting changes: {e}"}), 500
    
    def pull_commits(self, data):
        """Pull commits from source repository to target repository."""
        if 'source_repo' not in data or 'target_repo' not in data:
            return jsonify({"error": "Source and target repository names are required"}), 400
        
        source_repo = data['source_repo']
        target_repo = data['target_repo']
        
        if not self.validate_repo_name(source_repo) or not self.validate_repo_name(target_repo):
            return jsonify({"error": "Invalid repository name"}), 400
        
        source_graph_db_path = self.get_graph_db_path(source_repo)
        target_graph_db_path = self.get_graph_db_path(target_repo)
        
        if not os.path.exists(source_graph_db_path):
            return jsonify({"error": f"Source repository '{source_repo}' not found"}), 404
        
        if not os.path.exists(target_graph_db_path):
            self.create_repo({"name": target_repo})
        
        try:
            with open(source_graph_db_path, 'r') as f:
                source_graph_data = json.load(f)
            
            with open(target_graph_db_path, 'r') as f:
                target_graph_data = json.load(f)
            
            source_commits = source_graph_data.get("commits", {})
            source_changes = source_graph_data.get("changes", {})
            
            target_commit_ids = set(target_graph_data.get("commits", {}).keys())
            
            commit_order = []
            visited = set()
            
            def visit(commit_id):
                if commit_id in visited:
                    return
                visited.add(commit_id)
                
                parent_id = source_commits.get(commit_id, {}).get("parent_id")
                if parent_id:
                    visit(parent_id)
                
                commit_order.append(commit_id)
            
            for commit_id in source_commits:
                visit(commit_id)
            
            pulled_commits = 0
            skipped_commits = 0
            
            for commit_id in commit_order:
                if commit_id in target_commit_ids:
                    skipped_commits += 1
                    continue
                
                commit_data = source_commits[commit_id]
                
                parent_id = commit_data.get("parent_id")
                if parent_id and parent_id not in target_commit_ids:
                    continue
                
                files_dict = {}
                for file_path, file_hash in commit_data.get("files", {}).items():
                    content = self.get_object_content(source_repo, file_hash)
                    new_hash = self.store_object(target_repo, content)
                    files_dict[file_path] = new_hash
                
                target_graph_data["commits"][commit_id] = {
                    "message": commit_data.get("message", ""),
                    "author": commit_data.get("author", ""),
                    "timestamp": commit_data.get("timestamp", ""),
                    "parent_id": commit_data.get("parent_id"),
                    "files": files_dict
                }

                if commit_id in source_changes:
                    if "changes" not in target_graph_data:
                        target_graph_data["changes"] = {}
                    target_graph_data["changes"][commit_id] = source_changes[commit_id]
                
                target_commit_ids.add(commit_id)
                pulled_commits += 1
                
                if target_graph_data.get("HEAD") is None:
                    target_graph_data["HEAD"] = commit_id
                    target_graph_data["branches"]["main"] = commit_id
            
            with open(target_graph_db_path, 'w') as f:
                json.dump(target_graph_data, f, indent=2)
            
            return jsonify({
                "message": f"Pulled {pulled_commits} commits from '{source_repo}' to '{target_repo}'",
                "pulled_commits": pulled_commits,
                "skipped_commits": skipped_commits
            }), 200
        
        except Exception as e:
            return jsonify({"error": f"Error pulling commits: {e}"}), 500
    
    def clone_repo(self, data):
        """Clone a repository to a new one, copying all objects and history."""
        if 'source_repo' not in data or 'target_repo' not in data:
            return jsonify({"error": "Source and target repository names are required"}), 400
        
        source_repo = data['source_repo']
        target_repo = data['target_repo']
        
        if not self.validate_repo_name(source_repo) or not self.validate_repo_name(target_repo):
            return jsonify({"error": "Invalid repository name"}), 400
        
        source_repo_dir = self.get_repo_path(source_repo)
        source_graph_db_path = self.get_graph_db_path(source_repo)
        source_objects_dir = self.get_objects_dir(source_repo)
        
        target_repo_dir = self.get_repo_path(target_repo)
        
        if not os.path.exists(source_repo_dir) or not os.path.exists(source_graph_db_path):
            return jsonify({"error": f"Source repository '{source_repo}' not found"}), 404
        
        if os.path.exists(target_repo_dir):
            return jsonify({"error": f"Target repository '{target_repo}' already exists"}), 400
        
        try:
            self.create_repo({"name": target_repo})
            target_objects_dir = self.get_objects_dir(target_repo)
            target_graph_db_path = self.get_graph_db_path(target_repo)
            
            with open(source_graph_db_path, 'r') as f:
                source_graph_data = json.load(f)
            
            with open(target_graph_db_path, 'r') as f:
                target_graph_data = json.load(f)

            for root, dirs, files in os.walk(source_objects_dir):
                for dir_name in dirs:
                    target_dir = os.path.join(target_objects_dir, os.path.relpath(os.path.join(root, dir_name), source_objects_dir))
                    os.makedirs(target_dir, exist_ok=True)
                    
                for file_name in files:
                    source_file = os.path.join(root, file_name)
                    target_file = os.path.join(target_objects_dir, os.path.relpath(source_file, source_objects_dir))
                    
                    os.makedirs(os.path.dirname(target_file), exist_ok=True)
                    
                    shutil.copy2(source_file, target_file)
            
            target_graph_data["commits"] = source_graph_data.get("commits", {})
            target_graph_data["changes"] = source_graph_data.get("changes", {})
            target_graph_data["branches"] = source_graph_data.get("branches", {"main": None})
            target_graph_data["HEAD"] = source_graph_data.get("HEAD")
            
            with open(target_graph_db_path, 'w') as f:
                json.dump(target_graph_data, f, indent=2)
            
            commit_count = len(target_graph_data.get("commits", {}))
            
            file_set = set()
            for commit_id, commit_data in target_graph_data.get("commits", {}).items():
                for file_path in commit_data.get("files", {}).keys():
                    file_set.add(file_path)
            file_count = len(file_set)
            
            return jsonify({
                "message": f"Repository '{source_repo}' cloned to '{target_repo}' successfully",
                "commit_count": commit_count,
                "file_count": file_count
            }), 200
            
        except Exception as e:
            if os.path.exists(target_repo_dir):
                shutil.rmtree(target_repo_dir)
            return jsonify({"error": f"Error cloning repository: {e}"}), 500
    
    def delete_repo(self, repo_name):
        """Delete a repository."""
        repo_dir = self.get_repo_path(repo_name)
        
        if not os.path.exists(repo_dir):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            shutil.rmtree(repo_dir)
            return jsonify({"message": f"Repository '{repo_name}' deleted successfully"}), 200
        
        except Exception as e:
            return jsonify({"error": f"Error deleting repository: {e}"}), 500
    
    def get_commit_history(self, repo_name, file_path):
        """Get the history of changes for a specific file."""
        graph_db_path = self.get_graph_db_path(repo_name)
        
        if not os.path.exists(graph_db_path):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            with open(graph_db_path, 'r') as f:
                graph_data = json.load(f)
            
            commits = graph_data.get("commits", {})
            changes = graph_data.get("changes", {})
            
            history = []
            
            for commit_id, commit_data in commits.items():
                if commit_id in changes and file_path in changes[commit_id]:
                    change_info = changes[commit_id][file_path]
                    
                    history.append({
                        "commit_id": commit_id,
                        "message": commit_data.get("message"),
                        "author": commit_data.get("author"),
                        "timestamp": commit_data.get("timestamp"),
                        "status": change_info.get("status"),
                        "diff": change_info.get("diff") if change_info.get("status") == "modified" else None,
                        "previous_hash": change_info.get("previous_hash"),
                        "current_hash": change_info.get("current_hash")
                    })
            
            history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return jsonify(history)
        
        except Exception as e:
            return jsonify({"error": f"Error getting file history: {e}"}), 500
    
    def validate_repo_name(self, repo_name):
        """Validate repository name."""
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', repo_name))