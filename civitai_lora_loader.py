import hashlib
import json
import os
import requests
import sys
import time
from tqdm import tqdm

import folder_paths
import comfy.utils
from nodes import LoraLoader

from .CivitAI_Model import CivitAI_Model
from .utils import short_paths_map, model_path, get_model_ids


ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
LORA_PATH = folder_paths.folder_names_and_paths["loras"][0][0]
LORAS = folder_paths.folder_names_and_paths["loras"][0]

MSG_PREFIX = '\33[1m\33[34m[CivitAI] \33[0m'

class CivitAI_LORA_Loader:
    """
        Implements the CivitAI LORA Loader node for ComfyUI 
    """
    def __init__(self):
        self.lora_loader = None

    @classmethod
    def INPUT_TYPES(cls):
        loras = folder_paths.get_filename_list("loras")
        loras.insert(0, 'none')
        lora_paths = short_paths_map(LORAS)
        
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "lora_air": ("STRING", {"default": "{model_id}@{model_version}", "multiline": False}),
                "lora_name": (loras,),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),

            },
            "optional": {
                "api_key": ("STRING", {"default": None, "multiline": False}),
                "download_chunks": ("INT", {"default": 4, "min": 1, "max": 12, "step": 1}),
                "download_path": (list(lora_paths),),
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP")
    FUNCTION = "load_lora"

    CATEGORY = "CivitAI/Loaders"

    def load_lora(self, model, clip, lora_air, lora_name, strength_model, strength_clip, api_key=None, download_chunks=None, download_path=None, extra_pnginfo=None):

        if extra_pnginfo and 'workflow' in extra_pnginfo:
            extra_pnginfo['workflow']['extra'].setdefault('lora_airs', [])

        if not self.lora_loader:
            self.lora_loader = LoraLoader()
            
        if lora_name == 'none':
        
            lora_id = None
            version_id = None
            
            lora_id, version_id = get_model_ids(lora_air)
            print(f"CKPT_ID: {lora_id} VERSION: {version_id}")

            lora_paths = short_paths_map(LORAS)
            if download_path:
                if lora_paths.__contains__(download_path):
                    download_path = lora_paths[download_path]
                else:
                    download_path = LORAS[0] 
            
            civitai_model = CivitAI_Model(model_id=lora_id, model_version=version_id, model_types=["LORA", "LoCon"], token=api_key, save_path=download_path, model_paths=LORAS, download_chunks=download_chunks)
                
            if not civitai_model.download():
               return model, clip 
               
            lora_name = civitai_model.name
            if extra_pnginfo and 'workflow' in extra_pnginfo:
                air = f'{civitai_model.model_id}@{civitai_model.version}'
                if air not in extra_pnginfo['workflow']['extra']['lora_airs']: 
                    extra_pnginfo['workflow']['extra']['lora_airs'].append(air)
                    
        else:
        
            lora_path = model_path(lora_name, LORAS)
            
            model_id, version_id, details = CivitAI_Model.sha256_lookup(lora_path)
            
            if model_id and version_id and extra_pnginfo and 'workflow' in extra_pnginfo:
                air = f'{model_id}@{version_id}'
                if air not in extra_pnginfo['workflow']['extra']['lora_airs']: 
                    extra_pnginfo['workflow']['extra']['lora_airs'].append(air)
            
            print(f"{MSG_PREFIX}Loading LORA from disk: {lora_path}")
        
        model_lora, clip_lora = self.lora_loader.load_lora(model, clip, lora_name, strength_model, strength_clip)

        return model_lora, clip_lora, { "extra_pnginfo": extra_pnginfo }
