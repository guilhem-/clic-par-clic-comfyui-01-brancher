# Serveur d'images de l'organisation : ComfyUI, dans le cluster tgpu (carte graphique).
#   docker build -t comfyui:1 services/comfyui
# Versions épinglées : ComfyUI (archive de l'étiquette GitHub), PyTorch CUDA 13.0 (le pilote Windows de
# la machine, 581.95, fournit CUDA 13.0). Les dépendances de ComfyUI sont celles de son
# requirements.txt à cette étiquette (interface web, modèles de workflows et noyaux comfy-kitchen y
# sont épinglés). Aucun nœud personnalisé, pas de ComfyUI-Manager.
# Pilote CUDA : fourni par le runtime NVIDIA du nœud (bibliothèques de la machine), pas par l'image.
# Poids des modèles, entrées, sorties et réglages de l'interface : hors de l'image, dans le volume du
# nœud /modeles/comfyui (--base-directory), téléchargés par le Job comfyui-modeles (k8s.yaml).
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

# Compilateur C : Triton (livré avec PyTorch) compile au premier appel son module de pilote CUDA ;
# PyTorch 2.14 passe par Triton pour certaines opérations (bmm_outer_product de l'encodeur de texte).
# Sans gcc : « Failed to find C compiler » dès le premier CLIPTextEncode. Noyaux compilés gardés dans
# ~/.triton (HOME=/modeles/comfyui/user, k8s.yaml).
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 comfy
WORKDIR /opt/comfyui
USER comfy
ENV PYTHONUNBUFFERED=1
EXPOSE 8188
CMD ["python", "main.py", "--listen", "0.0.0.0", "--port", "8188", "--base-directory", "/modeles/comfyui"]
