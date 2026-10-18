# Brancher ComfyUI dans Open WebUI — le serveur d'images de l'organisation

Démonstration du module 1 de la série « Clic par clic » **Générer des images dans Open WebUI avec
ComfyUI** : les utilisateurs d'Open WebUI génèrent des images sur la carte graphique de
l'organisation, sans envoyer leurs demandes à un service extérieur.

Vidéo : {{video}}

## But

- **ComfyUI** tourne dans un conteneur, sur la machine à carte graphique (`comfyui/`), avec un
  modèle d'image sous licence Apache 2.0 (Z-Image Turbo, 8 étapes).
- Son **workflow** est exporté au **format API** (`workflows/texte-vers-image.json`) : un
  dictionnaire, une entrée par numéro de nœud, dont Open WebUI remplit les valeurs à chaque demande.
- **Open WebUI** est branché dans Panneau d'administration › Réglages › Images : adresse interne de
  ComfyUI, workflow, correspondance des nœuds, modèle, taille, étapes
  (`open-webui/reglages-images.md`, ou `installer.py`).
- Dans une conversation, l'utilisateur active « Image » ; le modèle de conversation rédige la
  description et appelle l'outil `generate_image` ; l'image calculée par ComfyUI est rangée parmi
  les fichiers d'Open WebUI.

| Fichier | Contenu |
|---|---|
| `comfyui/Dockerfile` | Image `comfyui:1` : Python 3.13, PyTorch 2.14.1 (CUDA 13.0), ComfyUI v0.41.0, aucun nœud personnalisé |
| `comfyui/k8s.yaml` | Déploiement (une copie, `Recreate` : une seule carte), service `comfyui:8188`, publication de l'interface |
| `workflows/texte-vers-image.json` | Workflow au **format API**, tel qu'exporté dans la vidéo (à téléverser dans Open WebUI) |
| `workflows/texte-vers-image.interface.json` | Le même workflow au format de l'interface de ComfyUI (à ouvrir dans ComfyUI) : modèle Comfy-Org « Z-Image Turbo int8 », sous-graphe décompressé en gardant les numéros 27, 28, 13, 3, 9 |
| `open-webui/reglages-images.md` | Tous les champs de la page Images, la correspondance et ses deux pièges |
| `installer.py` | Les mêmes réglages par l'API d'Open WebUI (bibliothèque standard de Python), essai, retour arrière |

## Prérequis

- Une machine avec une carte graphique NVIDIA (8 Go suffisent), Kubernetes avec le runtime
  `nvidia` (tourné sur k3d, cluster dédié à la carte), `kubectl`, Docker.
- Open WebUI 0.11 (tourné sur 0.11.3) joignant ComfyUI par le réseau du cluster, un compte
  **administrateur**, et un modèle de conversation capable d'appeler des outils.
- Les poids du modèle, dans le volume monté sur `/modeles/comfyui/models` (6,2 + 5,6 + 0,3 Go) :

| Dossier | Fichier | Source (Hugging Face, Apache 2.0) |
|---|---|---|
| `diffusion_models/` | `z_image_turbo_int8_convrot.safetensors` | `Comfy-Org/z_image_turbo` › `split_files/diffusion_models/` |
| `text_encoders/` | `qwen_3_4b_fp8_mixed.safetensors` | `Comfy-Org/z_image_turbo` › `split_files/text_encoders/` |
| `vae/` | `ae.safetensors` | `Comfy-Org/z_image_turbo` › `split_files/vae/` |

## Installation pas à pas

### 1. Le serveur d'images

```bash
docker build -t comfyui:1 comfyui            # quelques Go : PyTorch CUDA
k3d image import comfyui:1 -c <cluster>      # sans registre (ou poussez l'image dans le vôtre)
kubectl apply -f comfyui/k8s.yaml
kubectl -n comfyui rollout status deploy/comfyui
```

Adaptez `k8s.yaml` à votre cluster : nom d'hôte de l'Ingress, volume des modèles (`hostPath` ici).
L'interface de ComfyUI ne doit être ouverte qu'à l'administrateur : elle n'a pas de comptes.

### 2. Le workflow, dans ComfyUI

Ouvrez `workflows/texte-vers-image.interface.json` (glisser-déposer dans l'interface, ou
`python installer.py --comfyui` qui le range dans le panneau « Flux de travail »). Repérez les nœuds
par leur numéro (dans les Paramètres, cherchez « badge » : mode de badge d'identifiant de nœud, « Afficher tout »),
puis menu **Fichier › Exporter (API)** : c'est ce fichier-là, et non le format de l'interface,
qu'Open WebUI attend.

### 3. Open WebUI, à la main comme dans la vidéo

Panneau d'administration › Réglages › Images : suivez `open-webui/reglages-images.md` (activer,
moteur ComfyUI, « Base URL », vérifier, téléverser le workflow, correspondance, modèle, taille,
étapes, enregistrer).

### 3 bis. Open WebUI, par l'API

```bash
cp .env.example .env          # OWUI_URL, OWUI_JETON (administrateur), COMFYUI_URL…
python installer.py           # sauvegarde la configuration en place (images-avant.json), puis règle
python installer.py --essai   # une image d'essai, générée par Open WebUI
python installer.py --retablir   # revenir à la configuration sauvegardée
```

La page Images est un réglage **de toute l'instance** : `images-avant.json` garde la configuration
précédente, clés comprises (fichier ignoré par git, ne le partagez pas).

## Essai

Avec un compte utilisateur : nouvelle conversation, menu « Intégrations » › « Image », puis
« Une affiche pour la formation Sécurité au travail à Lyon : un casque de chantier et un gilet jaune,
style illustration, couleurs vives, sans texte. » (le modèle d'image écorche souvent les mots écrits dans l'image.) Dépliez l'appel `generate_image` : la description envoyée à
ComfyUI a été rédigée par le modèle de conversation. Une seconde demande donne une nouvelle image
(nouvelle graine).

## Sécurité

- ComfyUI n'a ni comptes ni clé : n'exposez son service qu'à Open WebUI (réseau du cluster) et son
  interface qu'aux administrateurs.
- Aucune demande ne quitte l'organisation : description, calcul et image restent dans le cluster.
- Aucun secret dans ce dépôt : `.env` et `images-avant.json` sont ignorés par git.

## Série

- Module suivant : **Le workflow de l'organisation** (charte graphique imposée dans le workflow,
  piège du lien écrasé) — `clic-par-clic-comfyui-02-workflow-organisation` (à paraître).
- Côté utilisateur : module « Génération et retouche d'images » de la formation Open WebUI.

## Licence

MIT (voir `LICENSE`). ComfyUI : GPL-3.0 ; modèle Z-Image Turbo : Apache 2.0 ; Open WebUI : sa
propre licence (le code cité dans la vidéo reste le sien, il n'est pas recopié ici).
