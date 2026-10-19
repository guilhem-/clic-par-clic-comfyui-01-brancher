# Open WebUI: Admin Panel › Settings › Images

State shown at the end of the video (Open WebUI 0.11.3). Labels are those of the English
interface.

## Create Image

| Field | Value | Note |
|---|---|---|
| Image Generation | on | setting of the whole instance |
| Image Generation Engine | ComfyUI | |
| Model | `z_image_turbo_int8_convrot.safetensors` | file name in ComfyUI's `models/diffusion_models/`; required |
| Image Size | `1024x1024` | width × height, written into node 13 |
| Steps | `8` | distilled model: 8 steps are enough; written into node 3 |
| Image Prompt Generation | unchanged | no effect when the model calls the `generate_image` tool |
| Base URL | `http://comfyui.comfyui.svc.cluster.local:8188` | address as seen **from the Open WebUI server**, no trailing slash: Open WebUI accepts `/view?…` image addresses only if they have exactly this origin |
| API Key | empty | ComfyUI has no authentication: do not publish it outside the cluster |
| ComfyUI Workflow | `workflows/text-to-image.json` | **API format** (ComfyUI menu File › Export (API)) |

## ComfyUI Workflow Nodes (node mapping)

| Row | Key | Node Ids | Workflow node |
|---|---|---|---|
| Prompt* | `text` | `27` | `CLIPTextEncode`, the text of the request |
| Model | `unet_name` | `28` | `UNETLoader`, the diffusion model loader |
| Width | `width` | `13` | `EmptySD3LatentImage`, the empty image |
| Height | `height` | `13` | same |
| Steps | `steps` | `3` | `KSampler`, the sampler |
| Seed | `seed` | `3` | same |

Two traps:

1. **The model key.** Open WebUI suggests `ckpt_name`, the key of the older loaders
   (`CheckpointLoaderSimple`). This workflow's loader expects `unet_name`. ComfyUI ignores an
   unknown key, without any error message: the model chosen in Open WebUI would never be applied.
2. **The seed.** Without the `seed` row, the exported seed (0) stays fixed: two identical requests
   give exactly the same image (ComfyUI even serves it again from its cache). With the row, Open
   WebUI draws a random seed for each request.

What Open WebUI does for each request: `backend/open_webui/utils/images/comfyui.py`
(function `_apply_workflow_nodes`, then `comfyui_create_image`) —
<https://github.com/open-webui/open-webui/blob/v0.11.3/backend/open_webui/utils/images/comfyui.py>.

## On the user's side

The **Image** switch (Integrations menu of the input field) only shows up if:

1. image generation is on (this page);
2. the user has the "Image Generation" permission (Admin Panel › Users › Groups › Default
   permissions);
3. the chat model has the "Image Generation" capability (Workspace › Models).

The chat model then writes the description and calls the built-in tool `generate_image`.
