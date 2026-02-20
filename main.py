import psutil
import os
import time
import argparse
import configparser
from collections import defaultdict

# -------------------------------
# Paths robustos
# -------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
src_folder = os.path.join(BASE_DIR, "src")
config_path = os.path.join(src_folder, "config.ini")

# -------------------------------
# Default KEYMAP (vanilla ejemplo)
# -------------------------------
default_keymap = {
    "w": 87,
    "a": 65,
    "s": 83,
    "d": 68,
    "sft": 16,
    "spc": 32,
    "o": 79,
    "c": 67,
    "esc": 27,
    "l": 76,
    "i": 73,
    "k": 75,
    "e": 69,
    "del": 46
}

# -------------------------------
# Default CONFIG
# -------------------------------
default_config = {
    "auto_close_tas": "0",
    "show_stats": "1"
}

# -------------------------------
# Crear config.ini si no existe
# -------------------------------
if not os.path.exists(config_path):
    print("⚠ config.ini no encontrado, creando archivo base...")

    os.makedirs(src_folder, exist_ok=True)

    config_create = configparser.ConfigParser()
    config_create["CONFIG"] = default_config
    config_create["KEYMAP"] = {k: str(v) for k, v in default_keymap.items()}

    with open(config_path, "w", encoding="utf-8") as f:
        config_create.write(f)

    print("✔ config.ini creado.")

# -------------------------------
# Leer config.ini
# -------------------------------
config = configparser.ConfigParser()

with open(config_path, "r", encoding="utf-8-sig") as f:
    config.read_file(f)

modified = False

# Asegurar CONFIG
if "CONFIG" not in config:
    print("⚠ Sección [CONFIG] faltante, agregando defaults...")
    config["CONFIG"] = default_config
    modified = True

# Asegurar KEYMAP
if "KEYMAP" not in config:
    raise ValueError("ERROR: No existe la sección [KEYMAP] en config.ini")

# Guardar si fue modificado
if modified:
    new_config = configparser.ConfigParser()
    new_config["CONFIG"] = config["CONFIG"]
    new_config["KEYMAP"] = config["KEYMAP"]

    with open(config_path, "w", encoding="utf-8") as f:
        new_config.write(f)

    config = new_config
    print("✔ config.ini actualizado automáticamente.")

# -------------------------------
# Variables finales
# -------------------------------
show_stats = config["CONFIG"].getboolean("show_stats", fallback=True)
auto_close_tas = config["CONFIG"].getboolean("auto_close_tas", fallback=False)

keymap = {k.lower(): int(v) for k, v in config["KEYMAP"].items()}
keymap_inv = {v: k for k, v in keymap.items()}

# -------------------------------
# Paths Pizza Tower
# -------------------------------
pt_original = r"D:/SteamLibrary/steamapps/common/Pizza Tower/PizzaTower.exe"
pt_tas = r"D:/SteamLibrary/steamapps/common/Pizza Tower1/PizzaTower.exe"
pt_path = os.path.join(os.environ["APPDATA"], "PizzaTower_GM2")

# -------------------------------
# Encontrar proceso
# -------------------------------
def find_running_pizza():
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == "pizzatower.exe":
                return proc
        except:
            pass
    return None

# -------------------------------
# Argumentos
# -------------------------------
parser = argparse.ArgumentParser(description="Convertir TAS TXT ↔ PTM automáticamente")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("-r", "--read", action="store_true")
group.add_argument("-w", "--write", action="store_true")
args = parser.parse_args()

# -------------------------------
# Contador de inputs
# -------------------------------
input_counter = defaultdict(int)

# =====================================================
# WRITE: TXT → PTM
# =====================================================
if args.write:

    if auto_close_tas:
        proc = find_running_pizza()
        if proc:
            running_exe = os.path.normpath(proc.info['exe'])
            if running_exe == os.path.normpath(pt_tas):
                print("✔ Cerrando Pizza Tower TAS...")
                proc.terminate()
                time.sleep(1)
                if proc.is_running():
                    proc.kill()

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

        # Detectar formato: sft,d [49]
        if "[" in stripped and "]" in stripped:
            parts = stripped.split("[")
            keys_part = parts[0].strip()
            duration = int(parts[1].replace("]", "").strip())

            keys = [k.strip() for k in keys_part.split(",") if k.strip()]

            if duration <= 0:
                raise ValueError("Duración debe ser mayor que 0")

            frame_codes = [str(keymap[k.lower()]) for k in keys if k.lower() in keymap]
            frame_line = ",".join(frame_codes) + ",\n"

            tas_output += frame_line

            for _ in range(duration - 1):
                tas_output += frame_line

            for key in keys:
                if key.lower() in keymap:
                    input_counter[key.lower()] += duration

        else:
            keys = [k.strip() for k in stripped.split(",") if k.strip()]
            frame_codes = [str(keymap[k.lower()]) for k in keys if k.lower() in keymap]
            frame_line = ",".join(frame_codes) + ",\n"
            tas_output += frame_line

            for key in keys:
                if key.lower() in keymap:
                    input_counter[key.lower()] += 1

    with open(tas_file, "w", encoding="utf-8") as out:
        out.write(tas_output)

    print("✔ TAS PTM generado.")

# =====================================================
# READ: PTM → TXT
# =====================================================
elif args.read:

    with open(tas_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    with open(tas_txt, "w", encoding="utf-8") as f:

        last_line = None
        repeat_count = 0

        for line in lines:
            line_content = line.rstrip("\n")

            if not line_content:
                continue

            parts = line_content.split(",")
            mapped_parts = []

            for p in parts:
                if not p.strip():
                    continue
                try:
                    k_int = int(p)
                    if k_int in keymap_inv:
                        mapped_parts.append(keymap_inv[k_int])
                        input_counter[keymap_inv[k_int]] += 1
                except:
                    pass

            current_line = ",".join(mapped_parts)

            if current_line == last_line:
                repeat_count += 1
            else:
                if last_line is not None:
                    if repeat_count > 1:
                        f.write(f"{last_line} [{repeat_count}]\n")
                    else:
                        f.write(f"{last_line}\n")
                last_line = current_line
                repeat_count = 1

        if last_line is not None:
            if repeat_count > 1:
                f.write(f"{last_line} [{repeat_count}]\n")
            else:
                f.write(f"{last_line}\n")

    print("✔ TXT generado.")

# =====================================================
# STATS
# =====================================================
if show_stats and input_counter:
    print("\n[INPUT STATS]")

    sorted_inputs = sorted(
        input_counter.items(),
        key=lambda x: x[1],
        reverse=True
    )

    for key, count in sorted_inputs:
        print(f"{key} -> {count} frames")
