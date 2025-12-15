import psutil
import os
import time
import argparse

# -------------------------------
# Configuración de teclas
# -------------------------------
keymaptak = {
    "w": 87, "a": 65, "s": 83, "d": 68,
    "shift": 16, " ": 32, "o": 79, "c": 67,
    "esc": 27,
    "l": 76, "i": 73, "k": 75, "e": 69,
}
keymap_inv = {v: k for k, v in keymaptak.items()}

# -------------------------------
# Paths conocidos
# -------------------------------
pt_original = r"D:/SteamLibrary/steamapps/common/Pizza Tower/PizzaTower.exe"
pt_tas      = r"D:/SteamLibrary/steamapps/common/Pizza Tower1/PizzaTower.exe"
pt_path = os.path.expandvars(r"%APPDATA%\PizzaTower_GM2")
tas_file = os.path.join(pt_path, "tas.ptm")
tas_txt = r"D:/Leon/Python/ptas/tas.txt"

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
group.add_argument("-r", "--read", action="store_true", help="Leer tas.ptm y generar tas.txt")
group.add_argument("-w", "--write", action="store_true", help="Tomar tas.txt y sobrescribir tas.ptm")
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
        frame_codes = [str(keymaptak.get(k.lower(), "")) for k in keys_in_line]
        tas_output += ",".join(frame_codes) + ",\n"

    # Guardar tas.ptm
    with open(tas_file, "w") as out:
        out.write(tas_output)

    print("✔ TAS PTM generado:", tas_file)

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
                else:
                    try:
                        k_int = int(p)
                        mapped_parts.append(keymap_inv.get(k_int, f"Unknown({k_int})"))
                    except ValueError:
                        mapped_parts.append(p)
            f.write(",".join(mapped_parts) + line_ending)

    print("✔ Archivo legible creado:", tas_txt)
