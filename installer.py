"""Brancher le serveur d'images ComfyUI dans Open WebUI, par l'API d'Open WebUI.

Fait ce que le module 1 de la série « Générer des images dans Open WebUI avec ComfyUI » fait à
l'écran, dans Panneau d'administration › Réglages › Images :
  1. génération d'image activée, moteur ComfyUI, adresse du serveur d'images (sans clé) ;
  2. workflow au format API (workflows/texte-vers-image.json) ;
  3. correspondance des nœuds : texte 27 (text), chargeur 28 (unet_name), image vide 13
     (width, height), échantillonneur 3 (steps, seed) ;
  4. modèle, taille et nombre d'étapes.

Usage :
  python installer.py               # sauvegarde la configuration en place (images-avant.json), puis règle
  python installer.py --essai       # génère une image d'essai par Open WebUI (adresse du fichier)
  python installer.py --retablir    # remet la configuration sauvegardée dans images-avant.json
  python installer.py --comfyui     # dépose le workflow (format de l'interface) dans ComfyUI

La sauvegarde images-avant.json contient la configuration complète de la page Images, clés
comprises : elle est ignorée par git, ne la partagez pas.

Réglages : fichier .env (voir .env.example) ; les variables d'environnement l'emportent.
Aucune dépendance : Python 3.10 ou plus récent, bibliothèque standard seulement.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ICI = pathlib.Path(__file__).resolve().parent
SAUVEGARDE = ICI / "images-avant.json"
VARIABLES = ("OWUI_URL", "OWUI_JETON", "COMFYUI_URL", "COMFYUI_INTERFACE", "MODELE", "TAILLE", "ETAPES")

# Correspondance des nœuds du workflow (numéros de workflows/texte-vers-image.json).
CORRESPONDANCE = [
    ("prompt", "text", "27"),
    ("model", "unet_name", "28"),
    ("width", "width", "13"),
    ("height", "height", "13"),
    ("steps", "steps", "3"),
    ("seed", "seed", "3"),
]


def reglages() -> dict:
    """Lit .env (clé=valeur), puis l'environnement, qui l'emporte."""
    r = {}
    env = ICI / ".env"
    if env.exists():
        for ligne in env.read_text(encoding="utf-8").splitlines():
            ligne = ligne.strip()
            if ligne and not ligne.startswith("#") and "=" in ligne:
                cle, valeur = ligne.split("=", 1)
                r[cle.strip()] = valeur.strip()
    for cle in VARIABLES:
        if os.environ.get(cle):
            r[cle] = os.environ[cle]
    return r


R = reglages()


def requete(methode: str, url: str, corps=None, entetes=None, brut: bytes | None = None):
    donnees = brut if brut is not None else (None if corps is None else json.dumps(corps).encode())
    req = urllib.request.Request(url, data=donnees, method=methode,
                                 headers={"Content-Type": "application/json", **(entetes or {})})
    try:
        with urllib.request.urlopen(req, timeout=300) as rep:
            texte = rep.read().decode()
    except urllib.error.HTTPError as e:
        sys.exit(f"{methode} {url} : {e.code} {e.read().decode()[:300]}")
    return json.loads(texte) if texte.strip().startswith(("{", "[")) else texte


def api(methode: str, chemin: str, corps=None):
    """Appel de l'API d'Open WebUI avec le jeton d'un administrateur."""
    if not R.get("OWUI_JETON"):
        sys.exit("OWUI_JETON manquant (.env) : jeton d'un compte administrateur d'Open WebUI.")
    return requete(methode, R["OWUI_URL"].rstrip("/") + chemin, corps,
                   {"Authorization": f"Bearer {R['OWUI_JETON']}"})


def installer() -> None:
    config = api("GET", "/api/v1/images/config")
    if not SAUVEGARDE.exists():
        SAUVEGARDE.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Configuration en place sauvegardée dans {SAUVEGARDE.name} (python installer.py --retablir)")
    workflow = (ICI / "workflows" / "texte-vers-image.json").read_text(encoding="utf-8")
    config.update({
        "ENABLE_IMAGE_GENERATION": True,
        "IMAGE_GENERATION_ENGINE": "comfyui",
        # Exactement l'origine qui sert les images, sans barre finale : Open WebUI n'accepte les
        # adresses /view?… de ComfyUI que si elles ont la même origine (contrôle anti-SSRF).
        "COMFYUI_BASE_URL": R.get("COMFYUI_URL", "").rstrip("/"),
        "COMFYUI_API_KEY": "",
        "COMFYUI_WORKFLOW": workflow,
        "COMFYUI_WORKFLOW_NODES": [{"type": t, "key": k, "node_ids": [n]} for t, k, n in CORRESPONDANCE],
        "IMAGE_GENERATION_MODEL": R.get("MODELE", "z_image_turbo_int8_convrot.safetensors"),
        "IMAGE_SIZE": R.get("TAILLE", "1024x1024"),
        "IMAGE_STEPS": int(R.get("ETAPES", "8")),
    })
    api("POST", "/api/v1/images/config/update", config)
    modeles = [m["id"] for m in api("GET", "/api/v1/images/models") or []]
    print(f"Open WebUI branché sur {config['COMFYUI_BASE_URL']} ; modèles vus dans ComfyUI : {', '.join(modeles) or 'aucun'}")


def essai() -> None:
    images = api("POST", "/api/v1/images/generations", {"prompt": "a red mug on a wooden table, flat illustration"})
    for image in images or []:
        print(f"Image : {R['OWUI_URL'].rstrip('/')}{image['url']}")


def retablir() -> None:
    if not SAUVEGARDE.exists():
        sys.exit(f"{SAUVEGARDE.name} introuvable : rien à rétablir.")
    api("POST", "/api/v1/images/config/update", json.loads(SAUVEGARDE.read_text(encoding="utf-8")))
    SAUVEGARDE.unlink()
    print("Configuration Images rétablie.")


def comfyui() -> None:
    """Dépose le workflow (format de l'interface) parmi les workflows de l'utilisateur de ComfyUI."""
    base = R.get("COMFYUI_INTERFACE", "").rstrip("/")
    if not base:
        sys.exit("COMFYUI_INTERFACE manquant (.env) : adresse de l'interface de ComfyUI dans le navigateur.")
    nom = urllib.parse.quote("workflows/Serveur d'images — texte vers image.json", safe="")
    corps = (ICI / "workflows" / "texte-vers-image.interface.json").read_bytes()
    # ComfyUI refuse une requête dont l'en-tête Origin ne correspond pas à son adresse.
    requete("POST", f"{base}/api/userdata/{nom}?overwrite=true", brut=corps, entetes={"Origin": base})
    print("Workflow « Serveur d'images — texte vers image » déposé dans ComfyUI (panneau Flux de travail).")


if __name__ == "__main__":
    if "--retablir" in sys.argv:
        retablir()
    elif "--essai" in sys.argv:
        essai()
    elif "--comfyui" in sys.argv:
        comfyui()
    else:
        installer()
