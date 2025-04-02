# VCS API Server

This is a modular version control system (VCS) API server built using Flask. It supports multiple backend implementations, allowing flexibility in how repositories and commits are managed. The current implementations include:

- **sqlite_fs**: Uses SQLite and the filesystem for storage.
- **graph_db**: Uses a custom graph database and objects for more advanced data relationships.

## Features
- **Modular Design**: The server allows easy integration of new implementations.
- **RESTful API**: Provides endpoints for repository management, commits, and version control.
- **API Key Authentication**: Secure access using API keys.
- **Cross-Origin Support**: CORS enabled for frontend applications.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/yourrepo/vcs-server.git
   cd vcs-server
   ```
2. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
3. Set up the environment variables:
   ```sh
   cp .env.example .env
   ```
   Then, update `.env` with your `VCS_API_KEY`.
4. Run the server:
   ```sh
   python server.py
   ```

## API Endpoints
### Authentication
All endpoints require an API key via the `X-API-Key` header. Alternatively you could set your server API-KEY to 'no-key' and it will authorize all operations without an API-KEY header.

### Implementations
- **List available implementations:** `GET /api/implementation`
- **Create a repository:** `POST /api/<implementation>/create_repo`
- **List repositories:** `GET /api/<implementation>/repos`
- **Get commit history:** `GET /api/<implementation>/commits/<repo_name>`
- **Get specific commit:** `GET /api/<implementation>/commit/<repo_name>/<commit_id>`
- **Check if commit exists:** `GET /api/<implementation>/check_commit/<repo_name>/<commit_id>`
- **Push a commit:** `POST /api/<implementation>/push`
- **Clone a repository:** `POST /api/<implementation>/clone`
- **Delete a repository:** `DELETE /api/<implementation>/delete_repo/<repo_name>`
- **Pull commits:** `POST /api/<implementation>/pull`
- **Get file history:** `GET /api/<implementation>/file_history/<repo_name>/<file_path>`

## Modular Implementation Registry
The VCS server is designed to be **highly modular**, enabling easy addition of new backend implementations. The **implementation registry** acts as a central hub to register and retrieve different VCS backends.

### How It Works
1. Implementations are registered in `implementations.py` using `register_implementation(name, class)`.
2. The `get_implementation(name)` function retrieves the corresponding backend.
3. The `list_implementations()` function lists all registered implementations.

### Current Implementations
```python
from implementations.sqlite_fs_impl import SQLiteFileSystemImplementation
from implementations.graph_db_impl import GraphDatabaseImplementation

register_implementation('sqlite_fs', SQLiteFileSystemImplementation)
register_implementation('graph_db', GraphDatabaseImplementation)
```

New implementations can be added by simply defining a class and registering it.

## License
This project is licensed under the MIT License.

## Contributing
Feel free to open issues or submit pull requests to improve the VCS API server!

Sole contributor @VileTBird

