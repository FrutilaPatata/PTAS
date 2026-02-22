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
    "up": 38,
    "down": 40,
    "left": 37,
    "right": 39,
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

if "CONFIG" not in config:
    print("⚠ Sección [CONFIG] faltante, agregando defaults...")
    config["CONFIG"] = default_config
    modified = True

if "KEYMAP" not in config:
    raise ValueError("ERROR: No existe la sección [KEYMAP] en config.ini")

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
# Cargar MULTIBIND (opcional)
# -------------------------------
multibind_raw = {}
multibind_map = {}
multibind_inv = {}

if "MULTIBIND" in config:
    for alias, keys_str in config["MULTIBIND"].items():
        raw_keys = [k.strip().lower() for k in keys_str.split(",") if k.strip()]
        multibind_raw[alias.lower()] = raw_keys

    def resolve_multibind(name, _stack=None):
        if _stack is None:
            _stack = []
        if name in _stack:
            raise ValueError(f"ERROR: Multibind circular detectado: {' -> '.join(_stack)} -> {name}")
        result = []
        for key in multibind_raw.get(name, [name]):
            if key in multibind_raw:
                result.extend(resolve_multibind(key, _stack + [name]))
            elif key in keymap:
                result.append(key)
            else:
                print(f"⚠ Multibind '{name}': tecla '{key}' no encontrada, ignorada")
        return result

    for alias in multibind_raw:
        multibind_map[alias] = resolve_multibind(alias)

    for alias, keys in multibind_map.items():
        if alias in keymap:
            multibind_inv[keymap[alias]] = keys
        else:
            print(f"⚠ Multibind '{alias}' no tiene keycode en [KEYMAP], ignorado en READ")

# -------------------------------
# Paths Macros
# -------------------------------
macros_folder = os.path.join(src_folder, "macros")
os.makedirs(macros_folder, exist_ok=True)

# -------------------------------
# Cargar macros (.pt.macro)
# -------------------------------
def load_macros():
    macros = {}
    if not os.path.isdir(macros_folder):
        return macros
    for filename in os.listdir(macros_folder):
        if filename.endswith(".pt.macro"):
            macro_name = filename[:-9]
            macro_path = os.path.join(macros_folder, filename)
            with open(macro_path, "r", encoding="utf-8") as f:
                macros[macro_name.lower()] = f.read().splitlines()
    return macros

# -------------------------------
# Expandir macros (con soporte de macros anidadas)
# -------------------------------
def expand_macros(lines, macros, _stack=None):
    if _stack is None:
        _stack = []
    expanded = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("@"):
            repeat = 1
            macro_ref = stripped[1:]
            if "[" in macro_ref and "]" in macro_ref:
                parts = macro_ref.split("[")
                macro_ref = parts[0].strip()
                repeat = int(parts[1].replace("]", "").strip())
            macro_name = macro_ref.lower()
            if macro_name not in macros:
                raise ValueError(f"ERROR: Macro '{macro_name}' no encontrada en /src/macros/")
            if macro_name in _stack:
                raise ValueError(f"ERROR: Macro circular detectada: {' -> '.join(_stack)} -> {macro_name}")
            macro_lines = macros[macro_name]
            for _ in range(repeat):
                expanded.extend(expand_macros(macro_lines, macros, _stack + [macro_name]))
        else:
            expanded.append(line)
    return expanded

# -------------------------------
# Orden canónico de teclas
# -------------------------------
CANONICAL_ORDER = ["sft", "w", "s", "a", "d", "spc", "o", "c"]

def normalize_key_order(line):
    suffix = ""
    core = line
    if line.endswith("]") and "[" in line:
        idx = line.rfind("[")
        suffix = " " + line[idx:]
        core = line[:idx].strip()
    keys = [k.strip() for k in core.split(",") if k.strip()]
    keys.sort(key=lambda k: CANONICAL_ORDER.index(k) if k in CANONICAL_ORDER else 9999)
    return ",".join(keys) + suffix

# -------------------------------
# Comprimir líneas repetidas al formato [N]
# -------------------------------
def compress_lines(lines):
    result = []
    last = None
    count = 0
    for line in lines:
        if line == last:
            count += 1
        else:
            if last is not None:
                result.append(f"{last} [{count}]" if count > 1 else last)
            last = line
            count = 1
    if last is not None:
        result.append(f"{last} [{count}]" if count > 1 else last)
    return result

# -------------------------------
# Construir índice de macros para READ mode
# -------------------------------
def build_macro_index(macros):
    index = {}
    for name in macros:
        expanded = expand_macros(macros[name], macros)
        raw = [normalize_key_order(l.strip()) for l in expanded if l.strip()]
        compressed = compress_lines(raw)
        if compressed:
            index[name] = compressed
    return dict(sorted(index.items(), key=lambda x: len(x[1]), reverse=True))

# -------------------------------
# Reemplazar secuencias en TXT por @macro
# -------------------------------
def replace_with_macros(txt_lines, macro_index):
    def expand_index_line(line):
        if line.startswith("@"):
            ref = line[1:].lower()
            if ref in macro_index:
                result = []
                for l in macro_index[ref]:
                    result.extend(expand_index_line(l))
                return result
        return [line]

    expanded_index = {}
    for name, lines in macro_index.items():
        flat = []
        for line in lines:
            flat.extend(expand_index_line(line))
        expanded_index[name] = compress_lines(flat)

    expanded_index = dict(sorted(expanded_index.items(), key=lambda x: len(x[1]), reverse=True))

    normalized = [normalize_key_order(l) if not l.startswith("@") else l for l in txt_lines]

    i = 0
    while i < len(normalized):
        matched = False
        for macro_name, macro_lines in expanded_index.items():
            mlen = len(macro_lines)
            if normalized[i:i + mlen] == macro_lines:
                normalized[i:i + mlen] = [f"@{macro_name}"]
                matched = True
                break
        if not matched:
            i += 1
    return normalized

# -------------------------------
# Paths Pizza Tower
# -------------------------------
pt_original = r"D:/SteamLibrary/steamapps/common/Pizza Tower/PizzaTower.exe"
pt_tas = r"D:/SteamLibrary/steamapps/common/Pizza Tower1/PizzaTower.exe"
pt_path = os.path.join(os.environ["APPDATA"], "PizzaTower_GM2")
tas_file = os.path.join(pt_path, "tas.ptm")
tas_txt = os.path.join(BASE_DIR, "tas.txt")

# -------------------------------
# Encontrar proceso Pizza Tower
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

    macros = load_macros()
    if macros:
        print(f"✔ Macros cargadas: {', '.join(macros.keys())}")

    with open(tas_txt, "r", encoding="utf-8") as file:
        lines = file.read().splitlines()

    lines = expand_macros(lines, macros)

    tas_output = ""

    def resolve_keys_to_codes(keys, duration=1):
        codes = []
        for k in keys:
            k = k.lower()
            if k in multibind_map:
                for sub_key in multibind_map[k]:
                    if sub_key in keymap:
                        codes.append(str(keymap[sub_key]))
                        input_counter[sub_key] += duration
            elif k in keymap:
                codes.append(str(keymap[k]))
                input_counter[k] += duration
        return codes

    for line in lines:
        stripped = line.strip()

        if not stripped:
            tas_output += "\n"
            continue

        if "[" in stripped and "]" in stripped:
            parts = stripped.split("[")
            keys_part = parts[0].strip()
            duration = int(parts[1].replace("]", "").strip())
            if duration <= 0:
                raise ValueError("Duración debe ser mayor que 0")
            keys = [k.strip() for k in keys_part.split(",") if k.strip()]
            frame_codes = resolve_keys_to_codes(keys, duration)
            frame_line = ",".join(frame_codes) + ",\n"
            for _ in range(duration):
                tas_output += frame_line
        else:
            keys = [k.strip() for k in stripped.split(",") if k.strip()]
            frame_codes = resolve_keys_to_codes(keys, 1)
            frame_line = ",".join(frame_codes) + ",\n"
            tas_output += frame_line

    with open(tas_file, "w", encoding="utf-8") as out:
        out.write(tas_output)

    print("✔ TAS PTM generado.")

# =====================================================
# READ: PTM → TXT
# =====================================================
elif args.read:

    macros = load_macros()
    macro_index = build_macro_index(macros) if macros else {}
    if macro_index:
        print(f"✔ Macros cargadas para detección: {', '.join(macro_index.keys())}")

    with open(tas_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    txt_lines = []
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
                    name = keymap_inv[k_int]
                    mapped_parts.append(name)
                    input_counter[name] += 1
                elif k_int in multibind_inv:
                    for sub_key in multibind_inv[k_int]:
                        mapped_parts.append(sub_key)
                        input_counter[sub_key] += 1
                else:
                    import ctypes
                    try:
                        vk = ctypes.windll.user32.MapVirtualKeyW(k_int, 2)
                        letter = chr(vk).lower() if vk else str(k_int)
                    except Exception:
                        letter = str(k_int)
                    # print(f"⚠ Keycode {k_int} ({letter.upper()}) no definido, poniendo como '{letter}'")
                    # mapped_parts.append(letter)
            except Exception:
                pass

        mapped_parts.sort(key=lambda k: CANONICAL_ORDER.index(k) if k in CANONICAL_ORDER else 9999)
        current_line = ",".join(mapped_parts)

        if current_line == last_line:
            repeat_count += 1
        else:
            if last_line is not None:
                txt_lines.append(f"{last_line} [{repeat_count}]" if repeat_count > 1 else last_line)
            last_line = current_line
            repeat_count = 1

    if last_line is not None:
        txt_lines.append(f"{last_line} [{repeat_count}]" if repeat_count > 1 else last_line)

    if macro_index:
        txt_lines = replace_with_macros(txt_lines, macro_index)

    with open(tas_txt, "w", encoding="utf-8") as f:
        for line in txt_lines:
            f.write(line + "\n")

    print("✔ TXT generado.")

# =====================================================
# STATS
# =====================================================
if show_stats and input_counter:
    print("\n[INPUT STATS]")
    sorted_inputs = sorted(input_counter.items(), key=lambda x: x[1], reverse=True)
    for key, count in sorted_inputs:
        print(f"{key} -> {count} frames")