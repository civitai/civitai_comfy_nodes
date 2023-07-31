import concurrent.futures
import os
import re
import json
import time
import threading
import hashlib
import requests
from tqdm import tqdm

import comfy.utils
import folder_paths


ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

MSG_PREFIX = '\33[1m\33[34m[CivitAI] \33[0m'
WARN_PREFIX = '\33[1m\33[34m[CivitAI]\33[0m\33[93m Warning: \33[0m'
ERR_PREFIX = '\33[1m\33[31m[CivitAI]\33[0m\33[1m Error: \33[0m'


class CivitAI_Model:
    '''
    CivitAI Model Class © Civitai 2023
    Written by Jordan Thompson

    Provides general model file downloading from CivitAI API v1
    '''
    api = 'https://civitai.com/api/v1'
    num_chunks = 8
    chunk_size = 1024
    max_retries = 120
    debug_response = False

    def __init__(self, model_id, save_path, model_paths, model_types=[], model_version=None, download_chunks=None, max_download_retries=None, warning=True, debug_response=False):
        self.model_id = model_id
        self.version = model_version
        self.type = None
        self.valid_types = model_types
        self.model_path = save_path
        self.model_paths = model_paths
        self.name = None
        self.name_friendly = None
        self.download_url = None
        self.file_details = None
        self.file_id = None
        self.file_sha256 = None
        self.file_size = 0
        self.trained_words = None
        self.warning = warning
        
        if download_chunks:
            self.num_chunks = int(download_chunks)

        if max_download_retries:
            self.max_retries = int(max_download_retries)
            
        if debug_response:
            self.debug_response = True

        self.details()

    def details(self):
    
        # CHECK FOR EXISTING MODEL DATA
        
        model_name = self.model_cached_name(self.model_id, self.version)
        if model_name and self.model_exists_disk(model_name):
            history_file_path = os.path.join(ROOT_PATH, 'download_history.json')
            if os.path.exists(history_file_path):
                with open(history_file_path, 'r', encoding='utf-8') as history_file:
                    download_history = json.load(history_file)

                    model_id_str = str(self.model_id)
                    version_id = int(self.version) if self.version else None
                    file_id = int(self.file_id) if self.file_id else None

                    if model_id_str in download_history:
                        file_details_list = download_history[model_id_str]
                        for file_details in file_details_list:
                            files = file_details.get('files')
                            model_version = file_details.get('id')
                            if model_version and model_version == version_id:
                                if files:
                                    for file in files:
                                        file_version = file.get('id')
                                        name = file.get('name')

                                        if file_id and file_id == file_version:
                                            self.name = name
                                            self.name_friendly = file.get('name_friendly')
                                            self.download_url = file.get('downloadUrl')
                                            self.trained_words = file.get('trained_words')
                                            self.file_details = file
                                            self.file_id = file_version
                                            self.model_id = self.model_id
                                            self.version = int(file.get('id'))
                                            self.type = filget.get('model_type', 'Model')
                                            self.file_size = file.get('sizeKB', 0) * 1024
                                            hashes = file.get('hashes')
                                            if hashes:
                                                self.file_sha256 = hashes.get('SHA256')
                                            return self.name, self.file_details

                                        elif self.model_exists_disk(name):
                                            self.name = name
                                            self.name_friendly = file.get('name_friendly')
                                            self.download_url = file.get('downloadUrl')
                                            self.trained_words = file.get('trained_words')
                                            self.file_details = file
                                            self.file_id = file_version
                                            self.model_id = self.model_id
                                            self.version = int(file.get('id'))
                                            self.type = file.get('model_type', 'Model')
                                            self.file_size = file.get('sizeKB', 0) * 1024
                                            hashes = file.get('hashes')
                                            if hashes:
                                                self.file_sha256 = hashes.get('SHA256')
                                            return self.name, self.file_details
                                            
                    del download_history
 
        # NO CACHE DATA FOUND | DOWNLOAD MODEL DETAILS

        model_url = f'{self.api}/models/{self.model_id}'
        response = requests.get(model_url)

        if response.status_code == 200:
            model_data = response.json()
            
            if self.debug_response:
                print(f"{MSG_PREFIX}API Response:")
                print(''); print('')
                from pprint import pprint
                pprint(model_data, indent=4)
                print(''); print('')
            
            model_versions = model_data.get('modelVersions')
            model_type = model_data.get('type', 'Model')
            self.type = model_type
            model_friendly_name = model_data.get('name', 'Unknown')

            if model_type not in self.valid_types:
                raise Exception(f"{ERR_PREFIX}The model you requested is not a valid `{', '.join(self.valid_types)}`. Aborting!")

            if self.version:
                for version in model_versions:
                    version_id = version.get('id')
                    files = version.get('files')
                    trained_words = version.get('trainedWords', [])
                    model_download_url = version.get('downloadUrl', '')
                    if version_id == self.version and files:
                        for file in files:
                            download_url = file.get('downloadUrl')
                            if download_url == model_download_url:
                                self.download_url = download_url
                                self.file_details = file
                                self.file_id = file.get('id')
                                self.name = file.get('name')
                                self.trained_words = trained_words
                                self.file_details.update({'model_type': self.type, "trained_words": trained_words})
                                self.file_size = file.get('sizeKB', 0) * 1024
                                hashes = self.file_details.get('hashes')
                                if hashes:
                                    self.file_sha256 = hashes.get('SHA256')
                                return self.download_url, self.file_details
            else:
                version = model_versions[0]
                if version:
                    version_id = version.get('id')
                    files = version.get('files')
                    model_download_url = version.get('downloadUrl', '')
                    trained_words = version.get('trainedWords', [])
                    for file in files:
                        download_url = file.get('downloadUrl')
                        if download_url == model_download_url:
                            self.download_url = download_url
                            self.file_details = file
                            self.file_id = file.get('id')
                            self.name = file.get('name')
                            self.trained_words = trained_words
                            self.file_details.update({'model_type': self.type, "trained_words": trained_words})
                            self.file_size = file.get('sizeKB', 0) * 1024
                            hashes = self.file_details.get('hashes')
                            if hashes:
                                self.file_sha256 = hashes.get('SHA256')
                            return self.download_url, self.file_details
    

        else:
            raise Exception(f"{ERR_PREFIX}No cached model or model data found, and unable to reach CivitAI! Response Code: {response.status_code}\n Please try again later.")

    def download(self):
    
        # DOWNLAOD BYTE CHUNK
        
        def download_chunk(chunk_id, url, chunk_size, start_byte, end_byte, file_path, total_pbar, comfy_pbar, max_retries=30):
            retries = 0
            retry_delay = 5
            chunk_complete = False
            downloaded_bytes = 0  # Track the downloaded bytes for the chunk

            while retries <= max_retries:
                try:
                    headers = {'Range': f'bytes={start_byte + downloaded_bytes}-{end_byte}'}  # Adjust the byte range
                    response = requests.get(url, headers=headers, stream=True, timeout=10)
                    if response.status_code == 206:
                        with open(file_path, 'r+b') as file:
                            if retries > 0:
                                print(f"{MSG_PREFIX}Chunk {chunk_id} re-established in {retry_delay}s")
                                total_pbar.update()
                                time.sleep(retry_delay * 10)
                                total_pbar.set_postfix_str('')

                            file.seek(start_byte + downloaded_bytes)  # Move to the correct position in the file
                            for chunk in response.iter_content(chunk_size=chunk_size):
                                file.write(chunk)
                                total_pbar.update(len(chunk))
                                comfy_pbar.update(len(chunk))
                                downloaded_bytes += len(chunk)
                                retries = 0
                                if start_byte + downloaded_bytes >= end_byte:
                                    chunk_complete = True
                                    break

                            comfy_pbar.set_postfix_str(f"Chunk {chunk_id}: {downloaded_bytes} bytes downloaded")
                    else:
                        raise Exception(f"{ERR_PREFIX}Unable to establish download connection.")
                except (requests.exceptions.RequestException, Exception) as e:
                    print(f"{WARN_PREFIX}Chunk {chunk_id} connection lost")
                    total_pbar.update()
                    time.sleep(retry_delay)
                    retries += 1
                    if retries > max_retries:
                        print(f"{ERR_PREFIX}Chunk {chunk_id} failed to download after {max_retries} retries.")
                        break

                if chunk_complete:
                    break  # Break the loop when the chunk is complete

            if not chunk_complete:
                raise Exception(f"{ERR_PREFIX}Unable to re-establish connection to CivitAI.")

                
        # GET FILE SIZE
        
        def get_total_file_size(url):
            response = requests.get(url, stream=True)
            content_length = response.headers.get('Content-Length')
            if content_length is not None and content_length.isdigit():
                return int(content_length)

            response = requests.get(url, headers={'Range': 'bytes=0-999999999'}, stream=True)
            content_range = response.headers.get('Content-Range')
            if content_range:
                total_bytes = int(re.search(r'/(\d+)', content_range).group(1))
                return total_bytes
                
            if self.file_size:
                return self.file_size

            return None

        # RESOLVE MODEL ID/VERSION TO FILENAME

        model_name = self.model_cached_name(self.model_id, self.version)
        
        if model_name:
            model_path = self.model_exists_disk(model_name)
            if model_path:
                model_sha256 = CivitAI_Model.calculate_sha256(model_path)
                if self.name == model_name:
                    print(f"{MSG_PREFIX}Loading {self.type}: {self.name} (https://civitai.com/models/{self.model_id}/?modelVersionId={self.version})")
                    print(f"{MSG_PREFIX}{self.type} SHA256: {model_sha256}")
                    print(f"{MSG_PREFIX}Loading {self.type} from disk: {model_path}")
                    self.name = model_name
                    return True

        if not self.name:
            response = requests.head(self.download_url)
            if 'Content-Disposition' in response.headers:
                content_disposition = response.headers['Content-Disposition']
                self.name = re.findall("filename=(.+)", content_disposition)[0].strip('"')
            else:
                self.name = self.download_url.split('/')[-1]

        # NO MODEL FOUND! | DOWNLOAD MODEL FROM CIVITAI

        print(f"{MSG_PREFIX}Downloading `{self.name}` from `{self.download_url}`")
        save_path = os.path.join(self.model_path, self.name) # Assume default comfy folder, unless we take user input on extra paths
        
        # EXISTING MODEL FOUND -- CHECK SHA256
        
        if os.path.exists(save_path):
            print(f"{MSG_PREFIX}{self.type} file already exists at: {save_path}")
            self.dump_file_details()
            existing_sha256 = CivitAI_Model.calculate_sha256(save_path)
            if existing_sha256 == self.file_sha256:
                print(f"{MSG_PREFIX}{self.type} SHA256: {existing_sha256}")
                return True
            else:
                print(f"{ERR_PREFIX}Existing {self.type} file's SHA256 does not match. Retrying download...")

        # NO MODEL OR MODEL DATA AVAILABLE -- DOWNLOAD MODEL FROM CIVITAI

        response = requests.head(self.download_url)
        total_file_size = total_file_size = get_total_file_size(self.download_url)

        response = requests.get(self.download_url, stream=True)
        if response.status_code != requests.codes.ok:
            raise Exception(f"{ERR_PREFIX}Failed to download {self.type} file from CivitAI. Status code: {response.status_code}")

        with open(save_path, 'wb') as file:
            file.seek(total_file_size - 1)
            file.write(b'\0')

        futures = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_chunks) as executor:
            total_pbar = tqdm(total=total_file_size, unit='B', unit_scale=True, unit_divisor=1024, leave=True)
            comfy_pbar = comfy.utils.ProgressBar(total_file_size)
            comfy_pbar.update(0)
            for i in range(self.num_chunks):
                start_byte = i * (total_file_size // self.num_chunks)
                end_byte = start_byte + (total_file_size // self.num_chunks) - 1
                if i == self.num_chunks - 1:
                    end_byte = total_file_size - 1
                future = executor.submit(download_chunk, i, self.download_url, self.chunk_size, start_byte, end_byte, save_path, total_pbar, comfy_pbar, self.max_retries)
                futures.append(future)

            for future in futures:
                future.result()
                
            total_pbar.close()

        model_sha256 = CivitAI_Model.calculate_sha256(save_path)
        if model_sha256 == self.file_sha256:
            print(f"{MSG_PREFIX}Loading {self.type}: {self.name} (https://civitai.com/models/{self.model_id}/?modelVersionId={self.version})")
            print(f"{MSG_PREFIX}{self.type} SHA256: {model_sha256}")
            self.dump_file_details()
            return True
        else:
            os.remove(save_path)  # Remove Invalid / Broken / Insecure download file
            raise Exception(f"{ERR_PREFIX}{self.type} file's SHA256 does not match expected value after retry. Aborting download.")
    
    # DUMP MODEL DETAILS TO DOWNLOAD HISTORY
    
    def dump_file_details(self):
        history_file_path = os.path.join(ROOT_PATH, 'download_history.json')

        if not self.file_details:
            return

        if os.path.exists(history_file_path):
            with open(history_file_path, 'r', encoding='utf-8') as history_file:
                download_history = json.load(history_file)
        else:
            download_history = {}

        model_id_str = str(self.model_id)
        if model_id_str in download_history:
            model_versions = download_history[model_id_str]
            for version_details in model_versions:
                if version_details.get('id') == self.version:
                    files = version_details.get('files', [])
                    for file_details in files:
                        if file_details.get('downloadUrl') == self.download_url:
                            return

                    version_details.setdefault('files', []).append(self.file_details)
                    break
            else:
                download_history[model_id_str].append({
                    'id': self.version,
                    'files': [self.file_details],
                })
        else:
            download_history[model_id_str] = [{
                'id': self.version,
                'files': [self.file_details],
            }]

        with open(history_file_path, 'w', encoding='utf-8') as history_file:
            json.dump(download_history, history_file, indent=4, ensure_ascii=False)
            
    # RESOLVE ID/VERSION TO FILENAME

    def model_cached_name(self, model_id, version_id):
        history_file_path = os.path.join(ROOT_PATH, 'download_history.json')

        if os.path.exists(history_file_path):
            with open(history_file_path, 'r') as history_file:
                download_history = json.load(history_file)
                model_id_str = str(model_id)
                version_id = int(version_id) if version_id else None
                if model_id_str in download_history:
                    file_details_list = download_history[model_id_str]
                    for file_details in file_details_list:                        
                        version = file_details.get('id')
                        files = file_details.get('files')
                        if files:
                            for file in files:
                                name = file.get('name')
                                if version_id and version_id == version:
                                    return name
                                elif self.model_exists_disk(name):
                                    return name
        return None
        

    # CEHCK FOR MODEL ON DISK

    def model_exists_disk(self, name):
        for path in self.model_paths:
            if path and name:
                full_path = os.path.join(path, name)
                if os.path.exists(full_path):                    
                    if os.path.getsize(full_path) <= 0:
                        os.remove(full_path)
                    else:
                        return full_path
        return False

    # CEHCK FOR MODEL ON DISK

    def model_path(filename, search_paths):
        filename, _ = os.path.splitext(filename)
        for path in search_paths:
            print(path)
            for root, dirs, files in os.walk(path):
                for file in files:
                    name, ext = os.path.splitext(file)
                    print(name)
                    if name.lower() == filename.lower():
                        return os.path.join(root, file)
        return None

    # CALCULATE SHA256

    @staticmethod
    def calculate_sha256(file_path):
        sha256_hash = hashlib.sha256()
        if file_path and os.path.exists(file_path):
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest().upper()
        return 0
        
    # STATIC HASH LOOKUP FOR MANUAL LOADING
    @staticmethod
    def sha256_lookup(file_path):
        hash_value = CivitAI_Model.calculate_sha256(file_path)

        history_file_path = os.path.join(ROOT_PATH, 'download_history.json')
        if os.path.exists(history_file_path):
            with open(history_file_path, 'r', encoding='utf-8') as history_file:
                download_history = json.load(history_file)

            for model_id, model_versions in download_history.items():
                for version in model_versions:
                    version_id = version.get('id')
                    for file_details in version.get('files', []):
                        if file_details and file_details.get('hashes', {}).get('SHA256', '').upper() == hash_value:
                            model_type = file_details.get('model_type', 'Model')
                            print(f"{MSG_PREFIX}Loading {model_type}: {os.path.basename(file_path)} (https://civitai.com/models/{model_id}/?modelVersionId={version_id})")
                            print(f"{MSG_PREFIX}{model_type} Sha256: {hash_value}")
                            return (model_id, version_id, file_details)

        api = f"{CivitAI_Model.api}/model-versions/by-hash/{hash_value}"
        response = requests.get(api)

        if response.status_code == 200:
            model_details = response.json()
            if model_details:
                model_id = model_details.get('modelId')
                version_id = model_details.get('id')
                model_info = model_details.get('model')
                trained_words = model_details.get('trainedWords', [])
                model_type = model_info.get('type', 'Model')
                if model_info:
                    model_type = model_info.get('type', 'Model')
                model_versions = model_details.get('files', [])
                for file_details in model_versions:
                    hashes = file_details.get('hashes')
                    if hashes and hash_value in hashes.values():
                        print(f"{MSG_PREFIX}Loading {model_type}: {os.path.basename(file_path)} (https://civitai.com/models/{model_id}/?modelVersionId={version_id})")
                        print(f"{MSG_PREFIX}{model_type} Sha256: {hash_value}")
                        file_details.update({"model_type": model_type, "trained_words": trained_words})
                        CivitAI_Model.push_download_history(model_id, model_type, file_details)
                        return (model_id, version_id, file_details)
                    else:
                        if CivitAI_Model.warning:
                            print(f"{WARN_PREFIX}Unable to determine `{os.path.basename(file_path)}` source on CivitAI.")
        else:
            if CivitAI_Model.warning:
                print(f"{WARN_PREFIX}Unable to determine `{os.path.basename(file_path)}` source on CivitAI.")

        return (None, None, None)

    # STATIC DOWNLOAD HISTORY PUSH

    @staticmethod
    def push_download_history(model_id, model_type, file_details):
        history_file_path = os.path.join(ROOT_PATH, 'download_history.json')

        if not file_details:
            return

        file_details['model_type'] = model_type

        if os.path.exists(history_file_path):
            with open(history_file_path, 'r', encoding='utf-8') as history_file:
                download_history = json.load(history_file)

                model_id_str = str(model_id)
                if model_id_str in download_history:
                    model_versions = download_history[model_id_str]
                    for version_details in model_versions:
                        if version_details.get('id') == file_details.get('id'):
                            files = version_details.get('files', [])
                            for file_info in files:
                                if file_info.get('downloadUrl') == file_details.get('downloadUrl'):
                                    return

                            version_details.setdefault('files', []).append(file_details)
                            break
                    else:
                        download_history[model_id_str].append({
                            'id': file_details.get('id'),
                            'files': [file_details],
                        })
                else:
                    download_history[model_id_str] = [{
                        'id': file_details.get('id'),
                        'files': [file_details],
                    }]
        else:
            download_history = {
                str(model_id): [{
                    'id': file_details.get('id'),
                    'files': [file_details],
                }]
            }

        with open(history_file_path, 'w', encoding='utf-8') as history_file:
            json.dump(download_history, history_file, indent=4, ensure_ascii=False)
