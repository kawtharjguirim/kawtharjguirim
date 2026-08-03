"""
prep_photo.py
Prépare une photo brute pour la conversion ASCII :
1. Retire l'arrière-plan (rembg)
2. Booste le contraste local (CLAHE) pour faire ressortir les reliefs du visage
3. Compose sur fond blanc pur (le blanc mappe vers l'espace vide de la rampe ASCII)

Usage: python prep_photo.py source-photo.png
Sortie: prepped/source-prepped.png (niveaux de gris)
"""
import sys
import os
import numpy as np
import cv2
from PIL import Image
from rembg import remove


def prep_photo(input_path: str, output_path: str) -> None:
    # 1. Charger l'image et retirer le fond
    with open(input_path, "rb") as f:
        input_bytes = f.read()

    print("Suppression de l'arrière-plan...")
    output_bytes = remove(input_bytes)

    # rembg renvoie un PNG RGBA
    rgba = Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")

    # 2. Composer sur fond blanc pur
    white_bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, rgba).convert("RGB")

    # 3. Passage en niveaux de gris + CLAHE (contraste local adaptatif)
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    cv2.imwrite(output_path, enhanced)
    print(f"Photo préparée -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python prep_photo.py <source-photo>")
        sys.exit(1)

    src = sys.argv[1]
    out = "prepped/source-prepped.png"
    prep_photo(src, out)
