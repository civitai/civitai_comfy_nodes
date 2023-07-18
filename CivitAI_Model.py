import os
import re
import json
import time
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
        
        Provides general moodel file downloading from CivitAI API v1
    '''
    api = 'https://civitai.com/api/v1'

    def __init__(self, model_id, model_type, save_paths, model_version=None):
        self.model_id = model_id
        self.version = model_version
        self.type = model_type
        self.model_path = save_paths[0]
        self.model_paths = save_paths
        self.name = None
        self.name_friendly = None
        self.download_url = None
        self.file_details = None
        self.file_sha256 = None

        self.details()

    def details(self):
        model_name = self.model_cached_name(self.model_id, self.version)
        if model_name and os.path.exists(os.path.join(self.model_path, model_name)):
            history_file_path = os.path.join(ROOT_PATH, 'download_history.json')
            if os.path.exists(history_file_path):
                with open(history_file_path, 'r', encoding='utf-8') as history_file:
                    download_history = json.load(history_file)

                    if str(self.model_id) in download_history:
                        file_details_list = download_history[str(self.model_id)]
                        for file_details in file_details_list:
                            if file_details.get('name') == model_name:
                                self.name = model_name
                                self.name_friendly = file_details.get('name_friendly')
                                self.download_url = file_details.get('downloadUrl')
                                self.file_details = file_details
                                self.file_details.update({'model_type': self.type})
                                self.model_id = self.model_id
                                self.version = int(file_details.get('id'))
                                hashes = file_details.get('hashes')
                                if hashes:
                                    self.file_sha256 = hashes.get('SHA256')
                                return self.name, self.file_details

                del download_history

            raise Exception(f"{ERR_PREFIX}Cached data for `{model_name}` not found in download_history.json!")

        model_url = f'{self.api}/models/{self.model_id}'
        response = requests.get(model_url)

        if response.status_code == 200:
            model_data = response.json()
            model_versions = model_data.get('modelVersions')
            model_type = model_data.get('type', 'Model')
            model_friendly_name = model_data.get('name', 'Unknown')

            if model_type != self.type:
                raise Exception(f"{ERR_PREFIX}The model you requested is not a valid `{self.type}`. Aborting!")

            if not self.version:
                latest_version = max(model_versions, key=lambda x: x['id'])
                self.version = latest_version['id']
                files = latest_version.get('files', {})
                if files:
                    self.name = files[0]['name']
                    self.download_url = files[0]['downloadUrl']
                    self.file_details = files[0]
                    self.file_details.update({'model_type': self.type})
                    hashes = self.file_details.get('hashes')
                    if hashes:
                        self.file_sha256 = hashes.get('SHA256')
                    return self.download_url, self.file_details

            else:
                files = None
                for version in model_versions:
                    version_files = version.get('files')
                    if version_files:
                        for file in version_files:
                            if file['id'] == int(self.version):
                                self.name = file.get('name')
                                self.download_url = file.get('downloadUrl')
                                self.file_details = file
                                self.file_details.update({'model_type': self.type})
                                hashes = self.file_details.get('hashes')
                                if hashes:
                                    self.file_sha256 = hashes.get('SHA256')
                                return self.download_url, self.file_details

                if files is None:
                    latest_version = max(model_versions, key=lambda x: x['id'])
                    self.version = latest_version['id']
                    files = latest_version.get('files', {})
                    if files:
                        self.name = files[0]['name']
                        self.download_url = files[0]['downloadUrl']
                        self.file_details = files[0]
                        self.file_details.update({'model_type': self.type})
                        self.file_sha256 = files[0]['hashes']['SHA256']
                        return self.download_url, files[0]

        else:
            raise Exception(f"{ERR_PREFIX}Unable to reach CivitAI! Response Code: {response.status_code}\n Please try again later.")

    def download(self):
        model_name = self.model_cached_name(self.model_id, self.version)

        if model_name:
            model_path = self.model_exists_disk(model_name)
            if model_path:
                model_sha256 = CivitAI_Model.calculate_sha256(model_path)
                print(f"{MSG_PREFIX}Loading {self.type}: {self.name} (https://civitai.com/models/{self.model_id}/?modelVersionId={self.version})")
                print(f"{MSG_PREFIX}{self.type} Sha256: {model_sha256}")
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

        print(f"{MSG_PREFIX}Downloading `{self.name}` from `{self.download_url}`")
        save_path = os.path.join(self.model_path, self.name)

        if os.path.exists(save_path):
            print(f"{MSG_PREFIX}{self.type} file already exists at: {save_path}")
            self.dump_file_details()
            existing_sha256 = CivitAI_Model.calculate_sha256(save_path)
            if existing_sha256 == self.file_sha256:
                print(f"{MSG_PREFIX}{self.type} file's SHA256 matches expected value.")
                return True
            else:
                print(f"{ERR_PREFIX}Existing {self.type} file's SHA256 does not match expected value. Retrying download...")

        response = requests.get(self.download_url, stream=True)

        if response.status_code == requests.codes.ok:
            file_size = int(response.headers.get('Content-Length', 0))

            with open(save_path, 'wb') as file:
                pbar = comfy.utils.ProgressBar(file_size)
                pbar.update(0)

                retry_for = time.time() + 60
                for chunk in tqdm(response.iter_content(chunk_size=1024), total=file_size // 1024, unit='KB',
                                  unit_divisor=1024, unit_scale=True):
                    while not chunk:
                        if time.time() > retry_for:
                            raise Exception(f"{ERR_PREFIX}Failed to download {self.type} file from CivitAI with Response Code {response.status_code}")

                        time.sleep(1)
                        chunk = response.iter_content(chunk_size=1024)

                    file.write(chunk)
                    pbar.update(len(chunk))

            model_sha256 = CivitAI_Model.calculate_sha256(save_path)
            if model_sha256 == self.file_sha256:
                print(f"{MSG_PREFIX}Loading {self.type}: {self.name} (https://civitai.com/models/{self.model_id}/?modelVersionId={self.version})")
                print(f"{MSG_PREFIX}{self.type} Sha256: {model_sha256}")
                self.dump_file_details()
                return True
            else:
                os.remove(save_path)
                raise Exception(f"{ERR_PREFIX}{self.type} file's SHA256 does not match expected value after retry. Aborting download.")

        elif response.status_code == requests.codes.not_found:
            print(f"{ERR_PREFIX}CivitAI is not reachable, or the file was not found.")
        else:
            print(f"{ERR_PREFIX}Failed to download {self.type} file from CivitAI. Status code: {response.status_code}")

        raise Exception(f"{ERR_PREFIX}Failed to download {self.type} file from CivitAI due to an unknown error.")

    def dump_file_details(self):
        history_file_path = os.path.join(ROOT_PATH, 'download_history.json')

        if not self.file_details:
            return

        if os.path.exists(history_file_path):
            with open(history_file_path, 'r', encoding='utf-8') as history_file:
                download_history = json.load(history_file)

                if str(self.model_id) in download_history:
                    model_files = download_history[str(self.model_id)]
                    model_files = [file for file in model_files if file is not None]
                    model_files.append(self.file_details)
                    download_history[str(self.model_id)] = model_files
                else:
                    download_history[str(self.model_id)] = [self.file_details]
        else:
            download_history = {str(self.model_id): [self.file_details]}

        with open(history_file_path, 'w', encoding='utf-8') as history_file:
            json.dump(download_history, history_file, indent=4, ensure_ascii=False)

    def model_cached_name(self, model_id, version_id):
        history_file_path = os.path.join(ROOT_PATH, 'download_history.json')

        if os.path.exists(history_file_path):
            with open(history_file_path, 'r') as history_file:
                download_history = json.load(history_file)

                if str(model_id) in download_history:
                    file_details = download_history[str(model_id)]

                    for file in file_details:
                        if file:
                            version = file.get('id')
                            name = file.get('name')
                            if version_id and version == int(version_id):
                                return_name = name
                            if self.model_exists_disk(name):
                                return name

        return None
        
    def model_exists_disk(self, name):
        for path in self.model_paths:
            if os.path.exists(os.path.join(path, name)):
                return os.path.join(path, name)
        return False

    @staticmethod
    def calculate_sha256(file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest().upper()

    @staticmethod
    def sha256_lookup(file_path):
        hash_value = CivitAI_Model.calculate_sha256(file_path)

        history_file_path = os.path.join(ROOT_PATH, 'download_history.json')
        if os.path.exists(history_file_path):
            with open(history_file_path, 'r', encoding='utf-8') as history_file:
                download_history = json.load(history_file)

                for model_id, files in download_history.items():
                    for file_details in files:
                        if file_details and file_details.get('hashes', {}).get('SHA256', '').upper() == hash_value:
                            version_id = file_details.get('id')
                            model_type = file_details.get('model_type', 'Model')
                            print(f"{MSG_PREFIX}Loading {model_type}: {os.path.basename(file_path)} (https://civitai.com/models/{model_id}/?modelVersionId={version_id})")
                            print(f"{MSG_PREFIX}{model_type} Sha256: {hash_value}")
                            return (model_id, file_details.get('id'), file_details)

        api = f"{CivitAI_Model.api}/model-versions/by-hash/{hash_value}"
        response = requests.get(api)

        if response.status_code == 200:
            model_details = response.json()
            print(model_details)
            if model_details:
                model_id = model_details.get('modelId')
                model_info = model_details.get('model')
                model_type = 'Model'
                if model_info:
                    model_type = model_info.get('type', 'Model')
                model_versions = model_details.get('files', [])
                for file_details in model_versions:
                    
                    hashes = file_details.get('hashes')
                    if hashes and hash_value in hashes.values():
                        version_id = file_details.get('id')
                        print(f"{MSG_PREFIX}Loading {model_type}: {os.path.basename(file_path)} (https://civitai.com/models/{model_id}/?modelVersionId={version_id})")
                        print(f"{MSG_PREFIX}{model_type} Sha256: {hash_value}")
                        CivitAI_Model.push_download_history(model_id, model_type, file_details)
                        return (model_id, file_details.get('id'), file_details)
                    else:
                        print(f"{WARN_PREFIX}Unable to determine `{os.path.basename(file_path)}` source on CivitAI.")
        else:
            print(f"{WARN_PREFIX}Unable to determine `{os.path.basename(file_path)}` source on CivitAI.")

        return (None, None, None)

    @staticmethod
    def push_download_history(model_id, model_type, file_details):
        history_file_path = os.path.join(ROOT_PATH, 'download_history.json')

        if not file_details:
            return
            
        file_details['model_type'] = model_type

        if os.path.exists(history_file_path):
            with open(history_file_path, 'r', encoding='utf-8') as history_file:
                download_history = json.load(history_file)

                if str(model_id) in download_history:
                    model_files = download_history[str(model_id)]
                    model_files = [file for file in model_files if file is not None]
                    model_files.append(file_details)
                    download_history[model_id] = model_files
                else:
                    download_history[str(model_id)] = [file_details]
        else:
            download_history = {str(model_id): [file_details]}

        with open(history_file_path, 'w', encoding='utf-8') as history_file:
            json.dump(download_history, history_file, indent=4, ensure_ascii=False)
