# Implementation registry for VCS backend

_implementations = {}

def register_implementation(name, implementation_class):
    """Register a VCS implementation with the given name."""
    _implementations[name] = implementation_class()

def get_implementation(name):
    """Get a registered VCS implementation by name."""
    return _implementations.get(name)

def list_implementations():
    """List all registered VCS implementations."""
    return list(_implementations.keys())

from implementations.sqlite_fs_impl import SQLiteFileSystemImplementation
from implementations.graph_db_impl import GraphDatabaseImplementation

register_implementation('sqlite_fs', SQLiteFileSystemImplementation)
register_implementation('graph_db', GraphDatabaseImplementation)