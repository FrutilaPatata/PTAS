import psutil
import os
import time
import argparse
import configparser

# -------------------------------
# Paths robustos
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_folder = os.path.join(BASE_DIR, "src")
keymap_path = os.path.join(src_folder, "keymap.ini")

# -------------------------------
# Config base ORIGINAL (vanilla)
# -------------------------------
default_keymap = {
    "up": 38,
    "down": 40,
    "left": 37,
    "right": 39,
    "z": 90,
    "x": 88,
    "c": 67
}

# -------------------------------
# Crear archivo si no existe
# -------------------------------
if not os.path.exists(keymap_path):
    print("⚠ keymap.ini no encontrado, creando configuración base...")

    os.makedirs(src_folder, exist_ok=True)

    config_create = configparser.ConfigParser()
    config_create["KEYMAP"] = {k: str(v) for k, v in default_keymap.items()}

    with open(keymap_path, "w", encoding="utf-8") as f:
        config_create.write(f)

    print("✔ keymap.ini creado automáticamente.")

# -------------------------------
# Leer archivo (anti-BOM)
# -------------------------------
config = configparser.ConfigParser()

with open(keymap_path, "r", encoding="utf-8-sig") as f:
    config.read_file(f)

if "KEYMAP" not in config:
    raise ValueError("ERROR: No existe la sección [KEYMAP] en keymap.ini")

# -------------------------------
# Validar duplicados y valores inválidos
# -------------------------------
modified = False
seen_values = {}

for key, value in config["KEYMAP"].items():
    try:
        value_int = int(value)
    except ValueError:
        print(f"⚠ Valor inválido en '{key}', restaurando default si existe.")
        if key in default_keymap:
            config["KEYMAP"][key] = str(default_keymap[key])
            modified = True
        continue

    if value_int in seen_values:
        print(f"⚠ Duplicado detectado ({value_int}) entre '{key}' y '{seen_values[value_int]}'.")
        if key in default_keymap:
            config["KEYMAP"][key] = str(default_keymap[key])
            modified = True
    else:
        seen_values[value_int] = key

if modified:
    with open(keymap_path, "w", encoding="utf-8") as f:
        config.write(f)
    print("✔ keymap.ini corregido automáticamente.")

keymap = {k.lower(): int(v) for k, v in config["KEYMAP"].items()}
keymap_inv = {v: k for k, v in keymap.items()}

# -------------------------------
# Paths conocidos
# -------------------------------
pt_original = r"D:/SteamLibrary/steamapps/common/Pizza Tower/PizzaTower.exe"
pt_tas      = r"D:/SteamLibrary/steamapps/common/Pizza Tower1/PizzaTower.exe"
pt_path = os.path.expandvars(r"%APPDATA%\PizzaTower_GM2")
tas_file = os.path.join(pt_path, "tas.ptm")
tas_txt = r"./tas.txt"

# -------------------------------
# Buscar Pizza Tower
# -------------------------------
def find_running_pizza():
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'].lower() == "pizzatower.exe":
                return proc
        except:
            pass
    return None

# -------------------------------
# Argumentos CLI
# -------------------------------
parser = argparse.ArgumentParser(description="Convertir TAS TXT ↔ PTM automáticamente")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-r", "--read", action="store_true")
group.add_argument("-w", "--write", action="store_true")
args = parser.parse_args()

# =========================================================
# WRITE: TXT → PTM (soporte 'w [5]')
# =========================================================
if args.write:

    proc = find_running_pizza()
    if proc is not None:
        running_exe = os.path.normpath(proc.info['exe'])
        if running_exe == os.path.normpath(pt_tas):
            print("✔ Cerrando Pizza Tower TAS abierto...")
            proc.terminate()
            time.sleep(1)
            if proc.is_running():
                proc.kill()
        elif running_exe == os.path.normpath(pt_original):
            print("⚠ Pizza Tower ORIGINAL abierto, no se cerrará.")
        else:
            print("⚠ Pizza Tower abierto desde path desconocido:", running_exe)

    if not os.path.isdir(pt_path):
        print("ERROR: No existe la carpeta PizzaTower_GM2.")
        exit()

    if not os.path.isfile(tas_file):
        open(tas_file, "w").close()

    with open(tas_txt, "r", encoding="utf-8") as file:
        lines = file.read().splitlines()

    tas_output = ""

    for line in lines:
        stripped = line.strip()

        if not stripped:
            tas_output += "\n"
            continue

        # Detectar formato "algo [n]"
        if "[" in stripped and stripped.endswith("]"):
            try:
                base_part, repeat_part = stripped.rsplit("[", 1)
                repeat_count = int(repeat_part[:-1].strip())
                base_part = base_part.strip()
            except ValueError:
                continue
        else:
            base_part = stripped
            repeat_count = 1

        keys_in_line = [k.strip() for k in base_part.split(",") if k.strip()]
        frame_codes = [str(keymap.get(k.lower(), "")) for k in keys_in_line]
        frame_line = ",".join(frame_codes) + ",\n"

        for _ in range(repeat_count):
            tas_output += frame_line

    with open(tas_file, "w", encoding="utf-8") as out:
        out.write(tas_output)

    print("✔ TAS PTM generated:", tas_file)

# =========================================================
# READ: PTM → TXT (compactar a 'w [5]')
# =========================================================
elif args.read:

    with open(tas_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    frames = []

    for line in lines:
        line_content = line.rstrip("\n")
        if not line_content:
            frames.append("")
            continue

        parts = line_content.split(",")
        mapped_parts = []

        for p in parts:
            if p.strip() == "":
                continue
            try:
                k_int = int(p)
                mapped_parts.append(keymap_inv.get(k_int, str(k_int)))
            except ValueError:
                pass

        frames.append(",".join(mapped_parts))

    with open(tas_txt, "w", encoding="utf-8") as f:
        i = 0
        while i < len(frames):
            current = frames[i]
            count = 1
            j = i + 1

            while j < len(frames) and frames[j] == current:
                count += 1
                j += 1

            if count > 1:
                f.write(f"{current} [{count}]\n")
            else:
                f.write(current + "\n")

            i = j

    print("✔ Created readable file:", tas_txt)