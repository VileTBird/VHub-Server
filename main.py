from flask import Flask, request, jsonify
from implementations import get_implementation
from flask_cors import CORS

import os
from functools import wraps
from dotenv import load_dotenv

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        load_dotenv()
        vcs_key = os.getenv('VCS_API_KEY')
        
        if vcs_key == "no-key":
            return f(*args, **kwargs)
            
        if not api_key or api_key != os.environ.get('VCS_API_KEY', 'demo-key'):
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
CORS(app) 

@app.route('/api/implementation', methods=['GET'])
@require_api_key
def list_implementations():
    """List all available VCS implementations."""
    from implementations import list_implementations
    return jsonify(list_implementations())

@app.route('/api/<implementation>/create_repo', methods=['POST'])
@require_api_key
def create_repo(implementation):
    """Create a new repository using the specified implementation."""
    data = request.json
    
    if not data or 'name' not in data:
        return jsonify({"error": "Repository name is required"}), 400
    
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.create_repo(data)

@app.route('/api/<implementation>/repos', methods=['GET'])
@require_api_key
def list_repos(implementation):
    """List all repositories for the specified implementation."""
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.list_repos()

@app.route('/api/<implementation>/commits/<repo_name>', methods=['GET'])
@require_api_key
def get_commits(implementation, repo_name):
    """Get all commits for a repository using the specified implementation."""
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.get_commits(repo_name)

@app.route('/api/<implementation>/commit/<repo_name>/<commit_id>', methods=['GET'])
@require_api_key
def get_commit(implementation, repo_name, commit_id):
    """Get details of a specific commit using the specified implementation."""
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.get_commit(repo_name, commit_id)

@app.route('/api/<implementation>/check_commit/<repo_name>/<commit_id>', methods=['GET'])
@require_api_key
def check_commit(implementation, repo_name, commit_id):
    """Check if a commit exists in the repository using the specified implementation."""
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.check_commit(repo_name, commit_id)

@app.route('/api/<implementation>/push', methods=['POST'])
@require_api_key
def push_commit(implementation):
    """Push a commit to a repository using the specified implementation."""
    data = request.json
    
    if not data or 'repo_name' not in data or 'id' not in data:
        return jsonify({"error": "Invalid commit data"}), 400
    
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.push_commit(data)

@app.route('/api/<implementation>/clone', methods=['POST'])
@require_api_key
def clone_repo(implementation):
    """Clone a repository using the specified implementation."""
    data = request.json
    
    if not data or 'source_repo' not in data or 'target_repo' not in data:
        return jsonify({"error": "Source and target repository names are required"}), 400
    
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.clone_repo(data)

@app.route('/api/<implementation>/delete_repo/<repo_name>', methods=['DELETE'])
@require_api_key
def delete_repo(implementation, repo_name):
    """Delete a repository using the specified implementation."""
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.delete_repo(repo_name)

@app.route('/api/<implementation>/pull', methods=['POST'])
@require_api_key
def pull_commits(implementation):
    """Pull commits from source repository to target repository using the specified implementation."""
    data = request.json
    
    if not data or 'source_repo' not in data or 'target_repo' not in data:
        return jsonify({"error": "Source and target repository names are required"}), 400
    
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.pull_commits(data)

from urllib.parse import unquote

@app.route('/api/<implementation>/file_history/<repo_name>/<path:file_path>', methods=['GET'])
@require_api_key
def get_file_history(implementation, repo_name, file_path):
    file_path = unquote(file_path)  # Decode URL-encoded path
    impl = get_implementation(implementation)
    if not impl:
        return jsonify({"error": f"Implementation '{implementation}' not found"}), 404
    
    return impl.get_commit_history(repo_name, file_path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)