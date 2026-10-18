# Open WebUI : Panneau d'administration › Réglages › Images

État montré à la fin de la vidéo (Open WebUI 0.11.3). Les libellés sont ceux de l'interface en
français ; certains ne sont pas traduits (« Base URL », « Prompt* », « Model »…).

## Création d'image

| Champ | Valeur | Remarque |
|---|---|---|
| Génération d'image | activé | réglage de toute l'instance |
| Moteur de génération d'image | ComfyUI | |
| Modèle | `z_image_turbo_int8_convrot.safetensors` | nom du fichier dans `models/diffusion_models/` de ComfyUI ; obligatoire |
| Taille de l'image | `1024x1024` | largeur × hauteur, écrites dans le nœud 13 |
| Étapes | `8` | modèle distillé : 8 étapes suffisent ; écrites dans le nœud 3 |
| Génération de prompts d'images | inchangé | sans effet quand le modèle appelle l'outil `generate_image` |
| Base URL | `http://comfyui.comfyui.svc.cluster.local:8188` | adresse vue **depuis le serveur Open WebUI**, sans barre finale : Open WebUI n'accepte les adresses d'images `/view?…` que si elles ont exactement cette origine |
| Clé API | vide | ComfyUI n'a pas d'authentification : ne le publiez pas hors du cluster |
| Workflow ComfyUI | `workflows/texte-vers-image.json` | **format API** (menu Fichier › Exporter (API) de ComfyUI) |

## Noeuds du workflow ComfyUI (correspondance)

| Ligne | Clé | ID des noeuds | Nœud du workflow |
|---|---|---|---|
| Prompt* | `text` | `27` | `CLIPTextEncode`, le texte de la demande |
| Model | `unet_name` | `28` | `UNETLoader`, le chargeur du modèle de diffusion |
| Width | `width` | `13` | `EmptySD3LatentImage`, l'image vide |
| Height | `height` | `13` | idem |
| Steps | `steps` | `3` | `KSampler`, l'échantillonneur |
| Seed | `seed` | `3` | idem |

Deux pièges :

1. **La clé du modèle.** Open WebUI propose `ckpt_name`, la clé des anciens chargeurs
   (`CheckpointLoaderSimple`). Le chargeur de ce workflow attend `unet_name`. Une clé inconnue est
   ignorée par ComfyUI, sans message d'erreur : le modèle choisi dans Open WebUI ne serait jamais
   appliqué.
2. **La graine.** Sans la ligne `seed`, la graine exportée (0) reste fixe : deux demandes identiques
   donnent exactement la même image (ComfyUI la ressert même depuis son cache). Avec la ligne, Open
   WebUI tire une graine au hasard à chaque demande.

Ce que fait Open WebUI à chaque demande : `backend/open_webui/utils/images/comfyui.py`
(fonction `_apply_workflow_nodes`, puis `comfyui_create_image`) —
<https://github.com/open-webui/open-webui/blob/v0.11.3/backend/open_webui/utils/images/comfyui.py>.

## Côté utilisateur

L'interrupteur « Image » (menu « Intégrations » du champ de saisie) n'apparaît que si :

1. la génération d'image est activée (cette page) ;
2. l'utilisateur a la permission « Génération d'image » (Panneau d'administration › Utilisateurs ›
   Groupes › Permissions par défaut) ;
3. le modèle de conversation a la capacité « Génération d'image » (Espace de travail › Modèles).

C'est alors le modèle de conversation qui rédige la description et appelle l'outil intégré
`generate_image`.
