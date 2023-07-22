# CivitAI_Loaders
<img width="400" src="https://i.postimg.cc/52zMsFZ2/Screenshot-2023-07-15-104434.png"> <img width="400" src="https://i.postimg.cc/XYHkkwg8/68747470733a2f2f692e706f7374696d672e63632f35327a4d73465a322f53637265656e73686f742d323032332d30372d31.png">

Load Checkpoints, and LORA models directly from CivitAI API (v1)

### MODEL AIR (?)
A Model AIR is either the model id, or a combination of model id at model version. Ex. `{model_id}@{version_id}`

#### Exmaples
This example would get the base model **Isabelle Fuhrman** `109395` and request the LORA version **isabellefuhrmanV02-000007.safetensors** `84321`
##### `109395@84321`</font>

While using only the ID would fetch **Isabelle Fuhrman** `109395` and find it's default model (which is the top most model an author designates)
##### `109395`</font>
