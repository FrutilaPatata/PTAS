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
# Config base ORIGINAL del juego
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
    print("⚠ keymap.ini no encontrado, creando configuración base del juego...")

    os.makedirs(src_folder, exist_ok=True)

    config = configparser.ConfigParser()
    config["KEYMAP"] = {k: str(v) for k, v in default_keymap.items()}

    with open(keymap_path, "w") as f:
        config.write(f)

    print("✔ keymap.ini creado automáticamente.")

# -------------------------------
# Cargar configuración
# -------------------------------
config = configparser.ConfigParser()
config.read(keymap_path)

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

# -------------------------------
# Guardar cambios si hubo correcciones
# -------------------------------
if modified:
    with open(keymap_path, "w") as f:
        config.write(f)
    print("✔ keymap.ini corregido automáticamente.")

# -------------------------------
# Crear diccionarios finales
# -------------------------------
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
# Función para encontrar Pizza Tower
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
# Argumentos de línea de comando
# -------------------------------
parser = argparse.ArgumentParser(description="Convertir TAS TXT ↔ PTM automáticamente")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-r", "--read", action="store_true", help="Read tas.ptm and generate tas.txt")
group.add_argument("-w", "--write", action="store_true", help="Take tas.txt and overwrite tas.ptm")
args = parser.parse_args()

# -------------------------------
# MODO WRITE: TXT → PTM
# -------------------------------
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
            print("⚠ Pizza Tower abierto desde path desconocido, no se cerrará:", running_exe) 

    if not os.path.isdir(pt_path):
        print("ERROR: No existe la carpeta PizzaTower_GM2.")
        exit()
    if not os.path.isfile(tas_file):
        open(tas_file, "w").close()

    # Leer tas.txt
    with open(tas_txt, "r") as file:
        lines = file.read().splitlines()

    # Convertir a keycodes
    tas_output = ""
    for line in lines:
        stripped = line.strip()
        if not stripped:
            tas_output += "\n"
            continue
        keys_in_line = [k.strip() for k in line.split(",") if k.strip()]
        frame_codes = [str(keymap.get(k.lower(), "")) for k in keys_in_line]
        tas_output += ",".join(frame_codes) + ",\n"

    # Guardar tas.ptm
    with open(tas_file, "w") as out:
        out.write(tas_output)

    print("✔ TAS PTM generated:", tas_file)

# -------------------------------
# MODO READ: PTM → TXT
# -------------------------------
elif args.read:
    with open(tas_file, "r") as f:
        lines = f.readlines()

    with open(tas_txt, "w") as f:
        for line in lines:
            line_ending = "\n" if line.endswith("\n") else ""
            line_content = line.rstrip("\n")
            if not line_content:
                f.write(line_ending)
                continue
            parts = line_content.split(",")
            mapped_parts = []
            for p in parts:
                if p.strip() == "":
                    mapped_parts.append("")
                elif ((p.strip() == "160") or (p.strip() == "161")) or (p.strip() == ","):
                    pass
                else:
                    try:
                        k_int = int(p)
                        mapped_parts.append(keymap_inv.get(k_int, f"{k_int}"))
                    except ValueError:
                        mapped_parts.append(p)
            f.write(",".join(mapped_parts) + line_ending)

    print("✔ Created readable file:", tas_txt)
