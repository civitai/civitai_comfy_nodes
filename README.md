# Civitai Comfy Nodes

Tired of manually downloading and moving models, LoRAs, and more to the right places?  
Sick of scouring Civitai for that one mystical LoRA someone was using to make that cool image?  
Want to be share a fully reproducable workflow?

**This is the set of nodes for you!**

## Nodes

<img width="300" src="https://github.com/civitai/comfy-nodes/assets/607609/a581144d-8e6f-4798-96ec-eba92ceef927"/>

### Checkpoint Loader
- Load checkpoints directly from Civitai using just a Model `AIR` (`model id` or `version id`)
- Resources used in images will be automatically detected on image upload
- Workflows copied from Civitai or shared via image metadata will include everything needed to generate the image including all resources

<img width="300" src="https://github.com/civitai/comfy-nodes/assets/607609/2038ecb5-ffc1-46d5-beee-6b11c72a2c12"/>

### LoRA Loader
- Load LoRAs directly from Civitai using just a LoRA `AIR` (`model id` or `version id`)
- Resources used in images will be automatically detected on image upload
- Workflows copied from Civitai or shared via image metadata will include everything needed to generate the image including all resources

### Embedding Loader _(Coming Soon)_
- Automatically detect textual inversions in prompts using `embedding:{air}` and download all the files needed.
- Resources used in images will be automatically detected on image upload
- Workflows copied from Civitai or shared via image metadata will include everything needed to generate the image including all resources

## `AIR`: AI Resource
An AIR is Civitai's way of universally referencing AI Resources. It follows the Uniform Resource Naming standard. If you're into that kinda thing, you can [read more about it here](https://github.com/civitai/civitai/wiki/AIR-%E2%80%90-Uniform-Resource-Names-for-AI). 

On Civitai, to keep things brief, an AIR is a combination of `model id` and optionally at a specific `model version`. Ex. `{model_id}` or `{model_id}@{version_id}`.

### Easy Copy AIRs
You can enable the display of AIRs on the site for easy copying from the Early Access settings of your [Account Settings](https://civitai.com/user/account).

<img width="400" src="https://github.com/civitai/comfy-nodes/assets/607609/ead8287f-7b11-4e2e-ac41-e0c83491bfbf"/>

<img width="300" src="https://github.com/civitai/comfy-nodes/assets/607609/2c4198b6-6d99-45e5-8d9d-f05a370d0582"/>


## Examples
This example would get the base model **Isabelle Fuhrman** `109395` and request the LORA version **isabellefuhrmanV02-000007.safetensors** `84321`
##### `109395@84321`</font>

While using only the ID would fetch **Isabelle Fuhrman** `109395` and find it's default model (which is the top most model an author designates)
##### `109395`</font>
