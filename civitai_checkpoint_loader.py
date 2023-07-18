import hashlib
import json
import os
import requests
import sys
import time
from tqdm import tqdm

import folder_paths
import comfy.sd
import comfy.utils
from nodes import CheckpointLoaderSimple

from .CivitAI_Model import CivitAI_Model


ROOT_PATH = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_PATH = folder_paths.folder_names_and_paths["checkpoints"][0][0]
CHECKPOINTS = folder_paths.folder_names_and_paths["checkpoints"][0]

MSG_PREFIX = '\33[1m\33[34m[CivitAI] \33[0m'
ERR_PREFIX = '\33[1m\33[31m[CivitAI]\33[0m\33[1m Error: \33[0m'


class CivitAI_Checkpoint_Loader:
    """
        Implements the CivitAI Checkpoint Loader node for ComfyUI 
    """
    def __init__(self):
        self.ckpt_loader = None

    @classmethod
    def INPUT_TYPES(cls):
        checkpoints = folder_paths.get_filename_list("checkpoints")
        checkpoints.insert(0, 'none')
        
        return {
            "required": {
                "ckpt_air": ("STRING", {"default": "{model_id}@{model_version}", "multiline": False}),
                "ckpt_name": (checkpoints,),
            },
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO"
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE")
    FUNCTION = "load_checkpoint"

    CATEGORY = "CivitAI/Loaders"

    def load_checkpoint(self, ckpt_air, ckpt_name, extra_pnginfo=None):

        if extra_pnginfo:
            if not extra_pnginfo['workflow']['extra'].__contains__('ckpt_airs'):
                extra_pnginfo['workflow']['extra'].update({'ckpt_airs': []})

        if not self.ckpt_loader:
            self.ckpt_loader = CheckpointLoaderSimple()
            
        if ckpt_name == 'none':
        
            ckpt_id = None
            version_id = None
            
            if '@' in ckpt_air:
                ckpt_id, version_id = ckpt_air.split('@')
            else:
                ckpt_id = ckpt_air
                
            ckpt_id = int(ckpt_id) if ckpt_id else None
            version_id = int(version_id) if version_id else None
            
            civitai_model = CivitAI_Model(model_id=ckpt_id, model_version=version_id, model_type="Checkpoint", save_paths=CHECKPOINTS)
                
            if not civitai_model.download():
               return None, None, None 
               
            ckpt_name = civitai_model.name
            if extra_pnginfo:
                air = f'{civitai_model.model_id}@{civitai_model.version}'
                if air not in extra_pnginfo['workflow']['extra']['ckpt_airs']: 
                    extra_pnginfo['workflow']['extra']['ckpt_airs'].append(air)
                    
        else:
        
            ckpt_path = None
            for path in CHECKPOINTS:
                if os.path.exists(os.path.join(path, ckpt_name)):
                    ckpt_path = os.path.join(path, ckpt_name)
                    
            
            model_id, version_id, details = CivitAI_Model.sha256_lookup(ckpt_path)
            
            if model_id and version_id and extra_pnginfo:
                air = f'{model_id}@{version_id}'
                if air not in extra_pnginfo['workflow']['extra']['ckpt_airs']: 
                    extra_pnginfo['workflow']['extra']['ckpt_airs'].append(air)
            
            print(f"{MSG_PREFIX}Loading checkpoint from disk: {ckpt_path}")
        
        out = self.ckpt_loader.load_checkpoint(ckpt_name=ckpt_name)
        
        from pprint import pprint
        pprint(out, indent=4)

        return out[0], out[1], out[2], { "extra_pnginfo": extra_pnginfo }



NODE_CLASS_MAPPINGS = {
    "CivitAI_Checkpoint_Loader": CivitAI_Checkpoint_Loader
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CivitAI_Checkpoint_Loader": "CivitAI Checkpoint Loader"
}