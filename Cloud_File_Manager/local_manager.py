import os

def list_local_items(path):
    """Return folders and files for Treeview display."""
    folders, files = [], []
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_dir():
                    folders.append(entry.name)
                else:
                    files.append(entry.name)
    except PermissionError:
        pass
    return sorted(folders), sorted(files)
