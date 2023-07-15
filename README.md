# CivitAI_LORA_Loader
Load LORA models directly from CivitAI API (v1)

### LORA Slug (?)
A LORA slug is either the model id, or a combination of model id at model version. Ex. `{model_id}@{version_id}`

#### Exmaples
This example would get the base model **Isabelle Fuhrman** `109395` and request the version **isabellefuhrmanV02-000007.safetensors** `84321`
##### `109395@84321`</font>

While using only the ID would fetch **Isabelle Fuhrman** `109395` and find it's default model (which is the top most model an author designates)
##### `109395`</font>
