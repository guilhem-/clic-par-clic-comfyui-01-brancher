"""Connect the ComfyUI image server to Open WebUI, through Open WebUI's API.

Does what module 1 of the "Image generation in Open WebUI with ComfyUI" series does on screen,
in Admin Panel > Settings > Images:
  1. image generation on, ComfyUI engine, address of the image server (no key);
  2. workflow in API format (workflows/text-to-image.json);
  3. node mapping: text 27 (text), loader 28 (unet_name), empty image 13 (width, height),
     sampler 3 (steps, seed);
  4. model, size and number of steps.

Usage:
  python setup_images.py               # back up the current configuration (images-config.backup.json), then apply
  python setup_images.py --test        # generate a test image through Open WebUI (address of the file)
  python setup_images.py --restore     # put back the configuration saved in images-config.backup.json
  python setup_images.py --comfyui     # drop the workflow (interface format) into ComfyUI

The backup images-config.backup.json holds the whole configuration of the Images page, keys
included: it is ignored by git, do not share it.

Settings: .env file (see .env.example); environment variables take precedence.
No dependency: Python 3.10 or newer, standard library only.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
BACKUP = HERE / "images-config.backup.json"
VARIABLES = ("OWUI_URL", "OWUI_TOKEN", "COMFYUI_URL", "COMFYUI_INTERFACE", "MODEL", "SIZE", "STEPS")

# Node mapping of the workflow (node numbers of workflows/text-to-image.json).
NODE_MAPPING = [
    ("prompt", "text", "27"),
    ("model", "unet_name", "28"),
    ("width", "width", "13"),
    ("height", "height", "13"),
    ("steps", "steps", "3"),
    ("seed", "seed", "3"),
]


def settings() -> dict:
    """Read .env (key=value), then the environment, which wins."""
    s = {}
    env = HERE / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                s[key.strip()] = value.strip()
    for key in VARIABLES:
        if os.environ.get(key):
            s[key] = os.environ[key]
    return s


S = settings()


def request(method: str, url: str, body=None, headers=None, raw: bytes | None = None):
    data = raw if raw is not None else (None if body is None else json.dumps(body).encode())
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            text = resp.read().decode()
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {url}: {e.code} {e.read().decode()[:300]}")
    return json.loads(text) if text.strip().startswith(("{", "[")) else text


def api(method: str, path: str, body=None):
    """Call Open WebUI's API with an administrator token."""
    if not S.get("OWUI_TOKEN"):
        sys.exit("OWUI_TOKEN missing (.env): token of an Open WebUI administrator account.")
    return request(method, S["OWUI_URL"].rstrip("/") + path, body,
                   {"Authorization": f"Bearer {S['OWUI_TOKEN']}"})


def setup() -> None:
    config = api("GET", "/api/v1/images/config")
    if not BACKUP.exists():
        BACKUP.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Current configuration saved to {BACKUP.name} (python setup_images.py --restore)")
    workflow = (HERE / "workflows" / "text-to-image.json").read_text(encoding="utf-8")
    config.update({
        "ENABLE_IMAGE_GENERATION": True,
        "IMAGE_GENERATION_ENGINE": "comfyui",
        # Exactly the origin that serves the images, without a trailing slash: Open WebUI accepts
        # ComfyUI's /view?… addresses only if they have the same origin (anti-SSRF check).
        "COMFYUI_BASE_URL": S.get("COMFYUI_URL", "").rstrip("/"),
        "COMFYUI_API_KEY": "",
        "COMFYUI_WORKFLOW": workflow,
        "COMFYUI_WORKFLOW_NODES": [{"type": t, "key": k, "node_ids": [n]} for t, k, n in NODE_MAPPING],
        "IMAGE_GENERATION_MODEL": S.get("MODEL", "z_image_turbo_int8_convrot.safetensors"),
        "IMAGE_SIZE": S.get("SIZE", "1024x1024"),
        "IMAGE_STEPS": int(S.get("STEPS", "8")),
    })
    api("POST", "/api/v1/images/config/update", config)
    models = [m["id"] for m in api("GET", "/api/v1/images/models") or []]
    print(f"Open WebUI connected to {config['COMFYUI_BASE_URL']}; models seen in ComfyUI: {', '.join(models) or 'none'}")


def test() -> None:
    images = api("POST", "/api/v1/images/generations", {"prompt": "a red mug on a wooden table, flat illustration"})
    for image in images or []:
        print(f"Image: {S['OWUI_URL'].rstrip('/')}{image['url']}")


def restore() -> None:
    if not BACKUP.exists():
        sys.exit(f"{BACKUP.name} not found: nothing to restore.")
    api("POST", "/api/v1/images/config/update", json.loads(BACKUP.read_text(encoding="utf-8")))
    BACKUP.unlink()
    print("Images configuration restored.")


def comfyui() -> None:
    """Drop the workflow (interface format) among the workflows of ComfyUI's user."""
    base = S.get("COMFYUI_INTERFACE", "").rstrip("/")
    if not base:
        sys.exit("COMFYUI_INTERFACE missing (.env): address of ComfyUI's interface in the browser.")
    name = urllib.parse.quote("workflows/Image server — text to image.json", safe="")
    body = (HERE / "workflows" / "text-to-image.interface.json").read_bytes()
    # ComfyUI refuses a request whose Origin header does not match its address.
    request("POST", f"{base}/api/userdata/{name}?overwrite=true", raw=body, headers={"Origin": base})
    print('Workflow "Image server — text to image" dropped into ComfyUI (Workflows panel).')


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console: dashes and quotes readable
    if "--restore" in sys.argv:
        restore()
    elif "--test" in sys.argv:
        test()
    elif "--comfyui" in sys.argv:
        comfyui()
    else:
        setup()
