import requests

def download_chunk(start_byte, end_byte, save_path, url):
    '''
        Download a chunk via byte range
    '''
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    response = requests.get(url, headers=headers, stream=True)
    with open(save_path, 'ab') as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)