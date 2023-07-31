import os

def short_paths_map(paths):
    short_paths_map_dict = {}
    for path in paths:
        if os.path.isfile(path) or os.path.isdir(path):
            path_parts = path.split(os.sep)
            if len(path_parts) >= 2:
                key = os.path.join(path_parts[-2], path_parts[-1])
            else:
                key = path
            short_paths_map_dict[key] = path
    return short_paths_map_dict
    
def model_path(filename, search_paths):
    filename = filename.lower().strip()
    for path in search_paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                name, ext = os.path.splitext(file)
                full_filename = name + ext
                if name.lower().strip() == filename or full_filename.lower().strip() == filename:
                    return os.path.join(root, file)
    return None
    