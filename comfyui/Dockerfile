# The organization's image server: ComfyUI, in the GPU cluster (k3d cluster "tgpu" in the series).
#   docker build -t comfyui:1 comfyui
# Pinned versions: ComfyUI (archive of the GitHub tag), PyTorch CUDA 13.0 (the machine's Windows
# driver, 581.95, provides CUDA 13.0). ComfyUI's dependencies are those of its requirements.txt at
# this tag (web interface, workflow templates and comfy-kitchen kernels are pinned there). No custom
# node, no ComfyUI-Manager.
# CUDA driver: provided by the node's NVIDIA runtime (the machine's libraries), not by the image.
# Model weights, inputs, outputs and interface settings: outside the image, in the node's volume
# /modeles/comfyui (--base-directory, see k8s.yaml); download the weights there (see README).
FROM python:3.13.16-slim

ARG TORCH=2.14.1
ARG TORCHVISION=0.29.1
ARG CUDA=cu130
ARG COMFYUI_VERSION=v0.41.0

RUN pip install --no-cache-dir torch==${TORCH} torchvision==${TORCHVISION} --index-url https://download.pytorch.org/whl/${CUDA}

ADD https://github.com/Comfy-Org/ComfyUI/archive/refs/tags/${COMFYUI_VERSION}.tar.gz /tmp/comfyui.tar.gz
RUN mkdir -p /opt/comfyui && tar -xzf /tmp/comfyui.tar.gz --strip-components=1 -C /opt/comfyui && rm /tmp/comfyui.tar.gz \
  && pip install --no-cache-dir -r /opt/comfyui/requirements.txt \
  && python -c "import torch, torchvision; assert torch.__version__ == '${TORCH}+${CUDA}', torch.__version__; assert torchvision.__version__.startswith('${TORCHVISION}')"

# C compiler: Triton (shipped with PyTorch) compiles its CUDA driver module on first use;
# PyTorch 2.14 goes through Triton for some operations (bmm_outer_product of the text encoder).
# Without gcc: "Failed to find C compiler" from the first CLIPTextEncode. Compiled kernels are kept
# in ~/.triton (HOME=/modeles/comfyui/user, k8s.yaml).
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 comfy
WORKDIR /opt/comfyui
USER comfy
ENV PYTHONUNBUFFERED=1
EXPOSE 8188
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--base-directory", "/modeles/comfyui"]
