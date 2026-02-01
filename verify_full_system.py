import os
import cv2
import numpy as np
from downmess_core import DownmessCore
from PIL import Image

def create_test_image(filename, size=(100, 100)):
    img = np.zeros((*size, 3), dtype=np.uint8)
    cv2.rectangle(img, (size[0]//4, size[1]//4), (3*size[0]//4, 3*size[1]//4), (255, 255, 255), -1)
    cv2.imwrite(filename, img)
    return filename

def test_system():
    core = DownmessCore()
    print("=== INICIANDO VERIFICACIÓN TOTAL DE DOWNMESS ===\n")

    # 1. Test IA: Resize
    print("[1/4] Probando Rescale...")
    img_path = create_test_image("verify_test.png")
    try:
        out = core.resize_image(img_path, 200, 200)
        if os.path.exists(out):
            res = cv2.imread(out)
            if res.shape[:2] == (200, 200):
                print(" -> [PASS] Rescale OK")
            else:
                print(f" -> [FAIL] Dimensiones incorrectas: {res.shape[:2]}")
        else:
            print(" -> [FAIL] Archivo de salida no encontrado")
    except Exception as e:
        print(f" -> [ERROR] {e}")

    # 2. Test IA: Upscale (Usando EDSR x2 para rapidez)
    print("\n[2/4] Probando AI Upscale (EDSR x2)...")
    small_img = create_test_image("verify_small.png", size=(20, 20))
    try:
        out = core.upscale_image_ai(small_img, model="edsr", scale=2)
        if os.path.exists(out):
            res = cv2.imread(out)
            if res.shape[:2] == (40, 40):
                print(" -> [PASS] AI Upscale OK")
            else:
                print(f" -> [FAIL] Dimensiones incorrectas: {res.shape[:2]}")
        else:
            print(" -> [FAIL] Archivo de salida no encontrado")
    except Exception as e:
        print(f" -> [ERROR] {e}")

    # 3. Test IA: BG Remove
    print("\n[3/4] Probando Background Removal...")
    try:
        out = core.remove_background(img_path)
        if os.path.exists(out):
            res = cv2.imread(out, cv2.IMREAD_UNCHANGED)
            if res.shape[2] == 4:
                print(" -> [PASS] BG Removal OK (Canal Alfa detectado)")
            else:
                print(" -> [FAIL] No se detectó canal alfa")
        else:
            print(" -> [FAIL] Archivo de salida no encontrado")
    except Exception as e:
        print(f" -> [ERROR] {e}")

    # 4. Test Core: Syntax Check
    print("\n[4/4] Verificando sintaxis de módulos principales...")
    files_to_check = ["downmess.py", "downmess_core.py", "downmess_mobile.py"]
    for f in files_to_check:
        if os.path.exists(f):
            print(f" -> Verificando {f}...")
            # Simple compile test
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    compile(file.read(), f, 'exec')
                print(f"    [OK] {f} compilado correctamente")
            except Exception as e:
                print(f"    [FAIL] Errores en {f}: {e}")
        else:
            print(f" -> [SKIP] {f} no encontrado")

    print("\n=== VERIFICACIÓN FINALIZADA ===")

if __name__ == "__main__":
    test_system()
