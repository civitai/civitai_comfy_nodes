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
                "download_chunks": ("INT", {"default": 4, "min": 1, "max": 12, "step": 1}),
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP")
    FUNCTION = "load_lora"

    CATEGORY = "CivitAI/Loaders"

    def load_lora(self, model, clip, lora_air, lora_name, strength_model, strength_clip, download_chunks=None, extra_pnginfo=None):

        if extra_pnginfo:
            if not extra_pnginfo['workflow']['extra'].__contains__('lora_airs'):
                extra_pnginfo['workflow']['extra'].update({'lora_airs': []})

        if not self.lora_loader:
            self.lora_loader = LoraLoader()
            
        if lora_name == 'none':
        
            lora_id = None
            version_id = None
            
            if '@' in lora_air:
                lora_id, version_id = lora_air.split('@')
            else:
                lora_id = lora_air
                
            lora_id = int(lora_id) if lora_id else None
            version_id = int(version_id) if version_id else None
            
            civitai_model = CivitAI_Model(model_id=lora_id, model_version=version_id, model_type="LORA", save_paths=LORAS, download_chunks=download_chunks)
                
            if not civitai_model.download():
               return model, clip 
               
            lora_name = civitai_model.name
            if extra_pnginfo:
                air = f'{civitai_model.model_id}@{civitai_model.version}'
                if air not in extra_pnginfo['workflow']['extra']['lora_airs']: 
                    extra_pnginfo['workflow']['extra']['lora_airs'].append(air)
                    
        else:
        
            lora_path = None
            for path in LORAS:
                if os.path.exists(os.path.join(path, lora_name)):
                    lora_path = os.path.join(path, lora_name)
                    
            
            model_id, version_id, details = CivitAI_Model.sha256_lookup(lora_path)
            
            if model_id and version_id and extra_pnginfo:
                air = f'{model_id}@{version_id}'
                if air not in extra_pnginfo['workflow']['extra']['lora_airs']: 
                    extra_pnginfo['workflow']['extra']['lora_airs'].append(air)
            
            print(f"{MSG_PREFIX}Loading LORA from disk: {lora_path}")
        
        model_lora, clip_lora = self.lora_loader.load_lora(model, clip, lora_name, strength_model, strength_clip)

        return model_lora, clip_lora, { "extra_pnginfo": extra_pnginfo }