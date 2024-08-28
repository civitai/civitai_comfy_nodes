import os
from urllib.parse import urlparse, parse_qs

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
    
def get_model_ids(url_or_air):
    """Extract the model ID and model version ID from a Civitai URL or AIR tag."""
    parsed_url = urlparse(url_or_air)
    if parsed_url.scheme and parsed_url.netloc:
        if "civitai.com" in parsed_url.netloc:
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) >= 2 and 'models' in path_parts:
                model_id = path_parts[path_parts.index('models') + 1]
                query_params = parse_qs(parsed_url.query)
                model_version_id = query_params.get('modelVersionId', [None])[0]
                return model_id, model_version_id
    elif '@' in url_or_air:
        air_parts = url_or_air.split('@')
        try:
            model_id = int(air_parts[0])
            model_version_id = int(air_parts[1]) if air_parts[1] else None
            return model_id, model_version_id
        except ValueError:
            raise ValueError(f"Invalid AIR tag format: {url_or_air}. Must be `model@modelVersionId`.")
    raise ValueError(f"Unable to determine model ID, and version ID from input: {url_or_air}")
