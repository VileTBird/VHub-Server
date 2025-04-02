import requests
import json
import hashlib
import argparse
import datetime
import sys
import os

BASE_URL = 'http://localhost:5000/api'

def print_response(response):
    print(f"Status: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    print("")

def list_implementations():
    response = requests.get(f"{BASE_URL}/implementation")
    print("\n=== Available Implementations ===")
    print_response(response)
    
    return response.json()

def create_repo(implementation, repo_name):
    response = requests.post(
        f"{BASE_URL}/{implementation}/create_repo",
        json={"name": repo_name}
    )
    print(f"\n=== Creating Repository '{repo_name}' ===")
    print_response(response)

def list_repos(implementation):
    response = requests.get(f"{BASE_URL}/{implementation}/repos")
    print("\n=== Repositories ===")
    print_response(response)

def generate_commit_id(data):
    message = data.get("message", "")
    author = data.get("author", "")
    timestamp = data.get("timestamp", "")
    parent_id = data.get("parent_id", "")
    
    commit_string = f"{message}{author}{timestamp}{parent_id}"
    return hashlib.sha1(commit_string.encode()).hexdigest()

def push_commit(implementation, repo_name, message, author, files, parent_id=None):
    timestamp = datetime.datetime.now().isoformat()
    
    data = {
        "repo_name": repo_name,
        "message": message,
        "author": author,
        "timestamp": timestamp,
        "files": files,
        "parent_id": parent_id
    }
    
    data["id"] = generate_commit_id(data)
    
    response = requests.post(f"{BASE_URL}/{implementation}/push", json=data)
    print(f"\n=== Pushing Commit to '{repo_name}' ===")
    print_response(response)
    
    return data["id"]

def get_commits(implementation, repo_name):
    """Get all commits for a repository."""
    response = requests.get(f"{BASE_URL}/{implementation}/commits/{repo_name}")
    print(f"\n=== Commits for '{repo_name}' ===")
    print_response(response)
    
    return response.json()

def get_commit(implementation, repo_name, commit_id):
    response = requests.get(f"{BASE_URL}/{implementation}/commit/{repo_name}/{commit_id}")
    print(f"\n=== Commit '{commit_id}' Details ===")
    print_response(response)

def check_commit(implementation, repo_name, commit_id):
    response = requests.get(f"{BASE_URL}/{implementation}/check_commit/{repo_name}/{commit_id}")
    print(f"\n=== Checking Commit '{commit_id}' ===")
    print_response(response)

def delete_repo(implementation, repo_name):
    response = requests.delete(f"{BASE_URL}/{implementation}/delete_repo/{repo_name}")
    print(f"\n=== Deleting Repository '{repo_name}' ===")
    print_response(response)

def clone_repo(implementation, source_repo, target_repo):
    data = {
        "source_repo": source_repo,
        "target_repo": target_repo
    }
    
    response = requests.post(f"{BASE_URL}/{implementation}/clone", json=data)
    print(f"\n=== Cloning Repository '{source_repo}' to '{target_repo}' ===")
    print_response(response)
    
    return response

def pull_commits(implementation, source_repo, target_repo):
    data = {
        "source_repo": source_repo,
        "target_repo": target_repo
    }
    
    response = requests.post(f"{BASE_URL}/{implementation}/pull", json=data)
    print(f"\n=== Pulling Commits from '{source_repo}' to '{target_repo}' ===")
    print_response(response)
    
    return response

def get_file_history(implementation, repo_name, file_path):
    response = requests.get(f"{BASE_URL}/{implementation}/file_history/{repo_name}/{file_path}")
    print(f"\n=== History for '{file_path}' in '{repo_name}' ===")
    print_response(response)
    
    return response.json()



def test_pull_functionality(implementation, source_repo, target_repo):
    print(f"\n=== Testing Pull Functionality with {implementation} ===")
    
    # Create source repo and add a commit
    create_repo(implementation, source_repo)
    
    files1 = {
        "file1.txt": {
            "hash": hashlib.sha1("Initial content".encode()).hexdigest(),
            "content": "Initial content"
        }
    }
    
    commit_id1 = push_commit(
        implementation,
        source_repo,
        "Initial commit in source",
        "Test User <test@example.com>",
        files1
    )
    
    # Create target repo (empty)
    create_repo(implementation, target_repo)
    
    # Pull commits from source to target
    pull_commits(implementation, source_repo, target_repo)
    
    # Verify both repos have the same commits
    source_commits = get_commits(implementation, source_repo)
    target_commits = get_commits(implementation, target_repo)
    
    print("\n=== Pull Verification (First Pull) ===")
    if len(source_commits) == len(target_commits):
        print("First pull successful: Same number of commits")
    else:
        print("First pull verification failed: Different number of commits")
    
    # Add new commit to source
    files2 = {
        "file1.txt": {
            "hash": hashlib.sha1("Updated content".encode()).hexdigest(),
            "content": "Updated content"
        },
        "file2.txt": {
            "hash": hashlib.sha1("New file content".encode()).hexdigest(),
            "content": "New file content"
        }
    }
    
    commit_id2 = push_commit(
        implementation,
        source_repo,
        "Second commit in source",
        "Test User <test@example.com>",
        files2,
        commit_id1
    )
    
    # Pull again
    pull_commits(implementation, source_repo, target_repo)
    
    # Verify again
    source_commits = get_commits(implementation, source_repo)
    target_commits = get_commits(implementation, target_repo)
    
    print("\n=== Pull Verification (Second Pull) ===")
    if len(source_commits) == len(target_commits):
        print("Second pull successful: Same number of commits")
    else:
        print("Second pull verification failed: Different number of commits")
    
    # Test file history
    get_file_history(implementation, target_repo, "file1.txt")
    
    # Cleanup
    delete_repo(implementation, source_repo)
    delete_repo(implementation, target_repo)

def run_comprehensive_test(implementation, repo_name):
    print(f"\n=== Running Comprehensive Test with {implementation} ===")
    
    # Run the full test first
    run_full_test(implementation, repo_name)
    
    # Add specific tests for pull functionality
    source_repo = f"{repo_name}_source"
    target_repo = f"{repo_name}_target"
    test_pull_functionality(implementation, source_repo, target_repo)
    
    # Add specific tests for file history
    test_repo = f"{repo_name}_history"
    create_repo(implementation, test_repo)
    
    # Create a file and make multiple changes to track history
    files1 = {
        "tracked_file.txt": {
            "hash": hashlib.sha1("Version 1".encode()).hexdigest(),
            "content": "Version 1"
        }
    }
    
    commit_id1 = push_commit(
        implementation,
        test_repo,
        "Initial version",
        "Test User <test@example.com>",
        files1
    )
    
    # Update file
    files2 = {
        "tracked_file.txt": {
            "hash": hashlib.sha1("Version 2".encode()).hexdigest(),
            "content": "Version 2"
        }
    }
    
    commit_id2 = push_commit(
        implementation,
        test_repo,
        "Update version",
        "Test User <test@example.com>",
        files2,
        commit_id1
    )
    
    # Update again
    files3 = {
        "tracked_file.txt": {
            "hash": hashlib.sha1("Version 3".encode()).hexdigest(),
            "content": "Version 3"
        }
    }
    
    commit_id3 = push_commit(
        implementation,
        test_repo,
        "Update version again",
        "Test User <test@example.com>",
        files3,
        commit_id2
    )
    
    # Get file history
    get_file_history(implementation, test_repo, "tracked_file.txt")
    
    # Cleanup
    delete_repo(implementation, test_repo)

def run_full_test(implementation, repo_name):
    print(f"\n=== Running Full Test with {implementation} on {repo_name} ===")
    
    create_repo(implementation, repo_name)
    
    list_repos(implementation)
    
    files = {
        "file1.txt": {
            "hash": hashlib.sha1("This is file 1".encode()).hexdigest(),
            "content": "This is file 1"
        },
        "file2.txt": {
            "hash": hashlib.sha1("This is file 2".encode()).hexdigest(),
            "content": "This is file 2"
        }
    }
    
    commit_id = push_commit(
        implementation,
        repo_name,
        "Initial commit",
        "Test User <test@example.com>",
        files
    )
    
    get_commits(implementation, repo_name)
    
    get_commit(implementation, repo_name, commit_id)
    
    check_commit(implementation, repo_name, commit_id)
    
    files = {
        "file1.txt": {
            "hash": hashlib.sha1("This is file 1 (updated)".encode()).hexdigest(),
            "content": "This is file 1 (updated)"
        },
        "file2.txt": {
            "hash": hashlib.sha1("This is file 2".encode()).hexdigest(),
            "content": "This is file 2"
        },
        "file3.txt": {
            "hash": hashlib.sha1("This is file 3".encode()).hexdigest(),
            "content": "This is file 3"
        }
    }
    
    commit_id2 = push_commit(
        implementation,
        repo_name,
        "Update file1 and add file3",
        "Test User <test@example.com>",
        files,
        commit_id
    )
    
    get_commits(implementation, repo_name)
    
    get_commit(implementation, repo_name, commit_id2)
    
    clone_target = f"{repo_name}_clone"
    clone_repo(implementation, repo_name, clone_target)
    
    list_repos(implementation)
    
    get_commits(implementation, clone_target)
    
    check_commit(implementation, clone_target, commit_id2)
    
    get_commit(implementation, clone_target, commit_id2)
    
    delete_repo(implementation, clone_target)

    delete_repo(implementation, repo_name)
    
    list_repos(implementation)

def test_clone_functionality(implementation, source_repo, target_repo):
    print(f"\n=== Testing Clone Functionality with {implementation} ===")
    
    create_repo(implementation, source_repo)
    
    files = {
        "file1.txt": {
            "hash": hashlib.sha1("Content for testing clone".encode()).hexdigest(),
            "content": "Content for testing clone"
        }
    }
    
    commit_id = push_commit(
        implementation,
        source_repo,
        "Commit for clone testing",
        "Test User <test@example.com>",
        files
    )
    
    clone_repo(implementation, source_repo, target_repo)
    
    list_repos(implementation)
    
    source_commits = get_commits(implementation, source_repo)
    clone_commits = get_commits(implementation, target_repo)
    
    print("\n=== Clone Verification ===")
    if source_commits == clone_commits:
        print("Clone successful: Source and target repositories have identical commits")
    else:
        print("Clone verification failed: Commits differ between source and target")
    
    delete_repo(implementation, source_repo)
    delete_repo(implementation, target_repo)
    
def main():
    parser = argparse.ArgumentParser(description='VCS Test Client')
    parser.add_argument('--implementation', '-i', default='sqlite_fs', help='VCS implementation to use')
    parser.add_argument('--repo', '-r', default='test_repo', help='Repository name to use for tests')
    parser.add_argument('--action', '-a', default='full', 
                        choices=['full', 'list_impl', 'create', 'list', 'push', 'get_commits', 
                                'get_commit', 'check_commit', 'delete', 'clone', 'test_clone',
                                'pull', 'test_pull', 'file_history'],
                        help='Action to perform')
    parser.add_argument('--target', '-t', help='Target repository name for clone/pull operation')
    parser.add_argument('--file', '-f', help='File path for file history')
    # Add to choices list
    choices=['full', 'comprehensive', 'list_impl', ...],

    
    args = parser.parse_args()
    
    if args.action == 'list_impl':
        list_implementations()
    elif args.action == 'full':
        run_full_test(args.implementation, args.repo)
    elif args.action == 'create':
        create_repo(args.implementation, args.repo)
    elif args.action == 'list':
        list_repos(args.implementation)
    elif args.action == 'push':
        files = {
            "test.txt": {
                "hash": hashlib.sha1("Test content".encode()).hexdigest(),
                "content": "Test content"
            }
        }
        push_commit(args.implementation, args.repo, "Test commit", "Test User", files)
    elif args.action == 'get_commits':
        get_commits(args.implementation, args.repo)
    elif args.action == 'get_commit':
        commits = get_commits(args.implementation, args.repo)
        if commits and len(commits) > 0:
            get_commit(args.implementation, args.repo, commits[0]['id'])
        else:
            print("No commits found")
    elif args.action == 'check_commit':
        commits = get_commits(args.implementation, args.repo)
        if commits and len(commits) > 0:
            check_commit(args.implementation, args.repo, commits[0]['id'])
        else:
            print("No commits found")
    elif args.action == 'delete':
        delete_repo(args.implementation, args.repo)
    elif args.action == 'clone':
        if not args.target:
            print("Error: Target repository name required for clone operation")
            sys.exit(1)
        clone_repo(args.implementation, args.repo, args.target)
    elif args.action == 'test_clone':
        if not args.target:
            args.target = f"{args.repo}_clone"
        test_clone_functionality(args.implementation, args.repo, args.target)
    elif args.action == 'pull':
        if not args.target:
            print("Error: Target repository name required for pull operation")
            sys.exit(1)
        pull_commits(args.implementation, args.repo, args.target)
    elif args.action == 'test_pull':
        if not args.target:
            args.target = f"{args.repo}_pull_test"
        test_pull_functionality(args.implementation, args.repo, args.target)
    elif args.action == 'file_history':
        if not args.file:
            print("Error: File path required for file history operation")
            sys.exit(1)
        get_file_history(args.implementation, args.repo, args.file)
    elif args.action == 'comprehensive':
        run_comprehensive_test(args.implementation, args.repo)

if __name__ == '__main__':
    main()