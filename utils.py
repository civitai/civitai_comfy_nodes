import os

def short_paths_map(paths):
    short_paths_map_dict = {}
    for path in paths:
        if os.path.isfile(path) or os.path.isdir(path):
            path_parts = path.split(os.sep)
            key = os.path.join(path_parts[-2], path_parts[-1])
            short_paths_map_dict[key] = path
    return short_paths_map_dict