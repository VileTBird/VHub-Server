import os
import sqlite3
import shutil
import datetime
import difflib
from flask import jsonify

from implementations.base import BaseVCSImplementation
from utils.path_utils import sanitize_path
from utils.hash_utils import calculate_hash

class SQLiteFileSystemImplementation(BaseVCSImplementation):
    """SQLite + File System implementation"""
    
    def __init__(self):
        """Initialize the implementation."""
        self.base_dir = os.path.abspath("./repositories/sqlite_fs")
        os.makedirs(self.base_dir, exist_ok=True)
    
    def get_repo_path(self, repo_name):
        """Get the path to a repository directory."""
        repo_dir = os.path.join(self.base_dir, sanitize_path(repo_name))
        return repo_dir
    
    def get_db_path(self, repo_name):
        """Get the path to a repository's database."""
        repo_dir = self.get_repo_path(repo_name)
        return os.path.join(repo_dir, "vcs.db")
    
    def init_repo_db(self, repo_name):
        """Initialize database for a repository."""
        db_path = self.get_db_path(repo_name)
        
        if not os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            CREATE TABLE commits (
                id TEXT PRIMARY KEY,
                message TEXT,
                author TEXT,
                timestamp TEXT,
                parent_id TEXT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE files (
                commit_id TEXT,
                file_path TEXT,
                file_hash TEXT,
                content TEXT,
                FOREIGN KEY (commit_id) REFERENCES commits(id),
                PRIMARY KEY (commit_id, file_path)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE changes (
                commit_id TEXT,
                file_path TEXT,
                status TEXT, -- 'added', 'modified', 'deleted'
                diff TEXT,   -- unified diff for modified files
                previous_hash TEXT,
                current_hash TEXT,
                FOREIGN KEY (commit_id) REFERENCES commits(id),
                PRIMARY KEY (commit_id, file_path)
            )
            ''')
            
            conn.commit()
            conn.close()
    
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
        self.init_repo_db(repo_name)
        
        return jsonify({"message": f"Repository '{repo_name}' created successfully"}), 200
    
    def list_repos(self):
        """List all repositories."""
        repos = []
        
        for repo_name in os.listdir(self.base_dir):
            repo_dir = self.get_repo_path(repo_name)
            db_path = self.get_db_path(repo_name)
            
            if os.path.isdir(repo_dir) and os.path.exists(db_path):
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM commits")
                    commit_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM files")
                    file_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT id, message, author, timestamp FROM commits ORDER BY timestamp DESC LIMIT 1")
                    last_commit = cursor.fetchone()
                    
                    last_commit_info = None
                    if last_commit:
                        last_commit_info = {
                            "id": last_commit[0],
                            "message": last_commit[1],
                            "author": last_commit[2],
                            "timestamp": last_commit[3]
                        }
                    
                    conn.close()
                    
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
        db_path = self.get_db_path(repo_name)
        
        if not os.path.exists(db_path):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, message, author, timestamp, parent_id FROM commits ORDER BY timestamp DESC")
            commits = cursor.fetchall()
            
            result = []
            for commit in commits:
                cursor.execute("SELECT COUNT(*) FROM changes WHERE commit_id = ?", (commit[0],))
                change_count = cursor.fetchone()[0]
                
                result.append({
                    "id": commit[0],
                    "message": commit[1],
                    "author": commit[2],
                    "timestamp": commit[3],
                    "parent_id": commit[4],
                    "change_count": change_count
                })
            
            conn.close()
            return jsonify(result)
        
        except Exception as e:
            return jsonify({"error": f"Error getting commits: {e}"}), 500
    
    def get_commit(self, repo_name, commit_id):
        """Get details of a specific commit with file changes."""
        db_path = self.get_db_path(repo_name)
        
        if not os.path.exists(db_path):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, message, author, timestamp, parent_id FROM commits WHERE id = ?", (commit_id,))
            commit = cursor.fetchone()
            
            if not commit:
                conn.close()
                return jsonify({"error": f"Commit '{commit_id}' not found"}), 404
            
            cursor.execute("SELECT file_path, file_hash, content FROM files WHERE commit_id = ?", (commit_id,))
            files = cursor.fetchall()
            
            cursor.execute("""
                SELECT file_path, status, diff, previous_hash, current_hash 
                FROM changes 
                WHERE commit_id = ?
            """, (commit_id,))
            changes = cursor.fetchall()
            
            files_data = {}
            for file_data in files:
                files_data[file_data[0]] = {
                    "hash": file_data[1],
                    "content": file_data[2]
                }
            
            changes_data = {}
            for change in changes:
                changes_data[change[0]] = {
                    "status": change[1],
                    "diff": change[2] if change[1] == "modified" else None,
                    "previous_hash": change[3],
                    "current_hash": change[4]
                }
            
            result = {
                "id": commit[0],
                "message": commit[1],
                "author": commit[2],
                "timestamp": commit[3],
                "parent_id": commit[4],
                "files": files_data,
                "changes": changes_data
            }
            
            conn.close()
            return jsonify(result)
        
        except Exception as e:
            return jsonify({"error": f"Error getting commit: {e}"}), 500
    
    def check_commit(self, repo_name, commit_id):
        """Check if a commit exists in the repository."""
        db_path = self.get_db_path(repo_name)
        
        if not os.path.exists(db_path):
            return jsonify({"exists": False, "error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM commits WHERE id = ? LIMIT 1", (commit_id,))
            exists = cursor.fetchone() is not None
            
            conn.close()
            return jsonify({"exists": exists})
        
        except Exception as e:
            return jsonify({"exists": False, "error": f"Error checking commit: {e}"}), 500
    
    def calculate_changes(self, conn, commit_data):
        """Calculate changes between this commit and its parent."""
        cursor = conn.cursor()
        parent_id = commit_data.get('parent_id')
        changes = {}
        
        if not parent_id:
            for file_path, file_info in commit_data['files'].items():
                changes[file_path] = {
                    "status": "added",
                    "diff": None,
                    "previous_hash": None,
                    "current_hash": file_info['hash']
                }
        else:
            cursor.execute("SELECT file_path, file_hash, content FROM files WHERE commit_id = ?", (parent_id,))
            parent_files = {row[0]: {"hash": row[1], "content": row[2]} for row in cursor.fetchall()}
            
            current_files = commit_data['files']
            
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
        db_path = self.get_db_path(repo_name)
        
        if not os.path.exists(repo_dir):
            os.makedirs(repo_dir, exist_ok=True)
            self.init_repo_db(repo_name)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM commits WHERE id = ? LIMIT 1", (data['id'],))
            if cursor.fetchone():
                conn.close()
                return jsonify({"message": f"Commit '{data['id']}' already exists"}), 200
            
            parent_id = data.get('parent_id')
            if parent_id:
                cursor.execute("SELECT 1 FROM commits WHERE id = ? LIMIT 1", (parent_id,))
                if not cursor.fetchone():
                    conn.close()
                    return jsonify({"error": f"Parent commit '{parent_id}' not found"}), 400
            
            cursor.execute(
                "INSERT INTO commits (id, message, author, timestamp, parent_id) VALUES (?, ?, ?, ?, ?)",
                (data['id'], data['message'], data['author'], data['timestamp'], data.get('parent_id'))
            )
            
            for file_path, file_info in data['files'].items():
                cursor.execute(
                    "INSERT INTO files (commit_id, file_path, file_hash, content) VALUES (?, ?, ?, ?)",
                    (data['id'], file_path, file_info['hash'], file_info['content'])
                )
            
            changes = self.calculate_changes(conn, data)
            
            for file_path, change_info in changes.items():
                cursor.execute(
                    """INSERT INTO changes 
                       (commit_id, file_path, status, diff, previous_hash, current_hash) 
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        data['id'], 
                        file_path, 
                        change_info['status'], 
                        change_info['diff'], 
                        change_info['previous_hash'], 
                        change_info['current_hash']
                    )
                )
            
            conn.commit()
            conn.close()
            
            return jsonify({
                "message": f"Commit '{data['id']}' pushed successfully",
                "changes": len(changes)
            }), 200
        
        except Exception as e:
            return jsonify({"error": f"Error pushing commit: {e}"}), 500
    
    def get_changes(self, repo_name, commit_id):
        """Get changes made in a specific commit."""
        db_path = self.get_db_path(repo_name)
        
        if not os.path.exists(db_path):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT 1 FROM commits WHERE id = ? LIMIT 1", (commit_id,))
            if not cursor.fetchone():
                conn.close()
                return jsonify({"error": f"Commit '{commit_id}' not found"}), 404
            
            cursor.execute("""
                SELECT file_path, status, diff, previous_hash, current_hash 
                FROM changes 
                WHERE commit_id = ?
            """, (commit_id,))
            changes = cursor.fetchall()
            
            result = {}
            for change in changes:
                result[change[0]] = {
                    "status": change[1],
                    "diff": change[2] if change[1] == "modified" else None,
                    "previous_hash": change[3],
                    "current_hash": change[4]
                }
            
            conn.close()
            return jsonify(result)
        
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
        
        source_db_path = self.get_db_path(source_repo)
        target_db_path = self.get_db_path(target_repo)
        
        if not os.path.exists(source_db_path):
            return jsonify({"error": f"Source repository '{source_repo}' not found"}), 404
        
        if not os.path.exists(target_db_path):
            self.create_repo({"name": target_repo})
        
        try:
            source_conn = sqlite3.connect(source_db_path)
            target_conn = sqlite3.connect(target_db_path)
            
            source_cursor = source_conn.cursor()
            target_cursor = target_conn.cursor()
            
            source_cursor.execute("""
                SELECT id, message, author, timestamp, parent_id 
                FROM commits 
                ORDER BY timestamp ASC
            """)
            source_commits = source_cursor.fetchall()
            
            target_cursor.execute("SELECT id FROM commits")
            target_commit_ids = set(row[0] for row in target_cursor.fetchall())
            
            pulled_commits = 0
            skipped_commits = 0
            
            for commit in source_commits:
                commit_id = commit[0]
                
                if commit_id in target_commit_ids:
                    skipped_commits += 1
                    continue
                
                parent_id = commit[4]
                if parent_id and parent_id not in target_commit_ids:
                    continue
                
                source_cursor.execute("""
                    SELECT file_path, file_hash, content 
                    FROM files 
                    WHERE commit_id = ?
                """, (commit_id,))
                files = source_cursor.fetchall()
                
                source_cursor.execute("""
                    SELECT file_path, status, diff, previous_hash, current_hash 
                    FROM changes 
                    WHERE commit_id = ?
                """, (commit_id,))
                changes = source_cursor.fetchall()
                
                target_cursor.execute(
                    "INSERT INTO commits (id, message, author, timestamp, parent_id) VALUES (?, ?, ?, ?, ?)",
                    commit
                )
                
                for file in files:
                    target_cursor.execute(
                        "INSERT INTO files (commit_id, file_path, file_hash, content) VALUES (?, ?, ?, ?)",
                        (commit_id, file[0], file[1], file[2])
                    )
                
                for change in changes:
                    target_cursor.execute(
                        """INSERT INTO changes 
                           (commit_id, file_path, status, diff, previous_hash, current_hash) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (commit_id, change[0], change[1], change[2], change[3], change[4])
                    )
                
                target_commit_ids.add(commit_id)
                pulled_commits += 1
            
            target_conn.commit()
            source_conn.close()
            target_conn.close()
            
            return jsonify({
                "message": f"Pulled {pulled_commits} commits from '{source_repo}' to '{target_repo}'",
                "pulled_commits": pulled_commits,
                "skipped_commits": skipped_commits
            }), 200
        
        except Exception as e:
            return jsonify({"error": f"Error pulling commits: {e}"}), 500
    
    def clone_repo(self, data):
        """Clone a repository to a new one by recreating all commits in order."""
        if 'source_repo' not in data or 'target_repo' not in data:
            return jsonify({"error": "Source and target repository names are required"}), 400
        
        source_repo = data['source_repo']
        target_repo = data['target_repo']
        
        if not self.validate_repo_name(source_repo) or not self.validate_repo_name(target_repo):
            return jsonify({"error": "Invalid repository name"}), 400
        
        source_repo_dir = self.get_repo_path(source_repo)
        source_db_path = self.get_db_path(source_repo)
        
        target_repo_dir = self.get_repo_path(target_repo)
        
        if not os.path.exists(source_repo_dir) or not os.path.exists(source_db_path):
            return jsonify({"error": f"Source repository '{source_repo}' not found"}), 404
        
        if os.path.exists(target_repo_dir):
            return jsonify({"error": f"Target repository '{target_repo}' already exists"}), 400
        
        try:
            self.create_repo({"name": target_repo})
            
            return self.pull_commits({
                "source_repo": source_repo,
                "target_repo": target_repo
            })
            
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
        db_path = self.get_db_path(repo_name)
        
        if not os.path.exists(db_path):
            return jsonify({"error": f"Repository '{repo_name}' not found"}), 404
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT c.id, c.message, c.author, c.timestamp, ch.status, ch.diff, ch.previous_hash, ch.current_hash
                FROM commits c
                JOIN changes ch ON c.id = ch.commit_id
                WHERE ch.file_path = ?
                ORDER BY c.timestamp DESC
            """, (file_path,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "commit_id": row[0],
                    "message": row[1],
                    "author": row[2],
                    "timestamp": row[3],
                    "status": row[4],
                    "diff": row[5] if row[4] == "modified" else None,
                    "previous_hash": row[6],
                    "current_hash": row[7]
                })
            
            conn.close()
            return jsonify(history)
        
        except Exception as e:
            return jsonify({"error": f"Error getting file history: {e}"}), 500
    
    def validate_repo_name(self, repo_name):
        """Validate repository name."""
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', repo_name))