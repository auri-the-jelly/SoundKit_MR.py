import os
import subprocess
import shutil
import struct
import time
from pathlib import Path
import pyfzf
import re
from collections import defaultdict

script_dir = os.getcwd()

extras_folder = "0_XTRA"
base_wems_folder = os.path.join(extras_folder, "0-CVS")
ignore_folder = os.path.join(extras_folder, "0-TESTS")
tools_folder = os.path.join(extras_folder, "0-TOOLS")
vgm_sub_folder = os.path.join(extras_folder, "0-VGCLI")


silent_file = os.path.join(ignore_folder, "0-Silent.wem")
input_wav_folder = "0-Put-CUSTOM-AUDIO-Here"
output_wem_folder = "2-Put-CUSTOM-WEMs-Here"
header_file = os.path.join(tools_folder, "header.bin")

# Core BNK input/output folders
original_bnk_folder = "1-Put-ORIGINAL-BNKs-Here"
modded_bnk_output = "3-Your-MODDED-BNK-Is-Here"

# Resolved absolute paths
original_bnk_path = os.path.join(script_dir, original_bnk_folder)
modded_bnk_output_path = os.path.join(script_dir, modded_bnk_output)

optional_folder = "x100-XTRAs-Are-Here"

# Option-specific parent folders
test_parent_folder = os.path.join(optional_folder, "x103-TEST-Wem-Stuff")
silent_parent_folder = os.path.join(optional_folder, "x104-SILENT-Wem-Stuff")
replace_parent_folder = os.path.join(optional_folder, "x105-REPLACED-Wem-Stuff")
isolated_parent_folder = os.path.join(optional_folder, "x106-ISOLATED-Wem-Stuff")
x107_parent = os.path.join(optional_folder, "x107-ASSIGN-Wem-Stuff")

# Subfoldersprocess-bnk
modded_bnk_folder = os.path.join(isolated_parent_folder, "A-Put-Modded-Bnk-Here")
vanilla_bnk_folder = os.path.join(isolated_parent_folder, "B-Put-Vanilla-Bnk-Here")
x107_input_folder = os.path.join(x107_parent, "A-Put-Audio-Files-To-ASSIGN-Here")
option107_temp_input = os.path.join(input_wav_folder, "Option107-Temp")

# Error / special folders
error_base_folder = "x200-ERROR-FILEs-Are-Here"
invalid_name_folder = os.path.join(error_base_folder, "x203-INVALID-NAME-Wems-Here")
dupe_id_folder = os.path.join(error_base_folder, "x202-DUPE-ID-Wems-Here")
no_match_folder = os.path.join(error_base_folder, "x204-Wems-With-NO-BNK-MATCH-Here")
audio_id_list_file = os.path.join(extras_folder, "AUDIO-ID-LIST.txt")
extracted_bnk_folder = "4-Your-EXTRACTED-BNKs-Are-Here"
cvs_renamed_wem_folder = os.path.join(extras_folder, "0-CVS", "2-RENAMED-WEMs-Are-Here")

# DEV folders
dev_root = os.path.join("0_XTRA", "0-DEV")
dev200_folder = os.path.join(dev_root, "DEV-200-AMPED-AUDIO")
dev202_root = os.path.join(dev_root, "DEV-202-REPAKED-BNKS")
dev202_input_bnks = os.path.join(dev202_root, "1-PUT-BNK-FILES-HERE")
dev203_folder = os.path.join(dev_root, "DEV-203-CONVERTED-WEMS")


ESSENTIAL_FOLDERS = [
    original_bnk_folder,
    input_wav_folder,
    output_wem_folder,
    modded_bnk_output,
    extracted_bnk_folder,
    extras_folder,
    ignore_folder,
    tools_folder,
    vgm_sub_folder,
    error_base_folder,
    invalid_name_folder,
    dupe_id_folder,
    no_match_folder,
    optional_folder,
    test_parent_folder,
    os.path.join(test_parent_folder, "A-Put-Wems-To-TEST-Here"),
    os.path.join(test_parent_folder, "B-Your-New-TEST-Wems-Are-Here"),
    silent_parent_folder,
    os.path.join(silent_parent_folder, "A-Put-Wems-To-SILENCE-Here"),
    os.path.join(silent_parent_folder, "B-Your-New-SILENCED-Wems-Are-Here"),
    replace_parent_folder,
    os.path.join(replace_parent_folder, "A-Put-Wems-To-REPLACE-Here"),
    os.path.join(replace_parent_folder, "B-Put-The-REPLACEMENT-Wem-Here"),
    os.path.join(replace_parent_folder, "C-Your-New-REPLACED-Wems-Are-Here"),
    isolated_parent_folder,
    modded_bnk_folder,
    vanilla_bnk_folder,
    x107_parent,
    x107_input_folder,
    option107_temp_input,
    dev_root,
    dev200_folder,
    dev202_root,
    dev202_input_bnks,
    dev203_folder,
]

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".ogg", ".m4a", ".flac", ".wem"}

MONO_HEADER = bytes(
    [
        0x52,
        0x49,
        0x46,
        0x46,
        0x58,
        0xB0,
        0x04,
        0x00,
        0x57,
        0x41,
        0x56,
        0x45,
        0x66,
        0x6D,
        0x74,
        0x20,
        0x18,
        0x00,
        0x00,
        0x00,
        0xFE,
        0xFF,
        0x01,
        0x00,
        0x80,
        0xBB,
        0x00,
        0x00,
        0x00,
        0x77,
        0x01,
        0x00,
        0x02,
        0x00,
        0x10,
        0x00,
        0x06,
        0x00,
        0x00,
        0x00,
        0x01,
        0x41,
        0x00,
        0x00,
        0x68,
        0x61,
        0x73,
        0x68,
        0x10,
        0x00,
        0x00,
        0x00,
        0xA5,
        0x6A,
        0x88,
        0xAA,
        0xB7,
        0xBD,
        0x54,
        0xD3,
        0xEC,
        0x3C,
        0xAC,
        0x9D,
        0x65,
        0xE1,
        0xCD,
        0x72,
    ]
)

STEREO_HEADER = bytes(
    [
        0x52,
        0x49,
        0x46,
        0x46,
        0x00,
        0x00,
        0x00,
        0x00,
        0x57,
        0x41,
        0x56,
        0x45,
        0x66,
        0x6D,
        0x74,
        0x20,
        0x18,
        0x00,
        0x00,
        0x00,
        0xFE,
        0xFF,
        0x02,
        0x00,
        0x80,
        0xBB,
        0x00,
        0x00,
        0x00,
        0x77,
        0x01,
        0x00,
        0x04,
        0x00,
        0x10,
        0x00,
        0x06,
        0x00,
        0x00,
        0x00,
        0x02,
        0x31,
        0x00,
        0x00,
        0x68,
        0x61,
        0x73,
        0x68,
        0x10,
        0x00,
        0x00,
        0x00,
        0x46,
        0x26,
        0xE0,
        0xBF,
        0x91,
        0x29,
        0x78,
        0xDD,
        0x78,
        0x67,
        0x99,
        0x9C,
        0xA4,
        0x66,
        0xBA,
        0x21,
        0x6A,
        0x75,
        0x6E,
        0x6B,
        0x0C,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x4A,
        0x55,
        0x4E,
        0x4B,
        0x04,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
    ]
)


def main():
    ensure_essential_folders()
    fzf = pyfzf.FzfPrompt()
    while True:
        options = [
            "0. Convert custom audio files to WEM format",
            "1. BNK tools (1-1 create, 1-2 extract+replace, 1-3 extract+rename)",
            "q. Quit",
        ]
        options_prompt = fzf.prompt(options, "--cycle --layout reverse")
        if not options_prompt:
            print("Exiting...")
            return
        selected = options_prompt[0]
        if selected.startswith("0."):
            convert_wav_to_wem()
        elif selected.startswith("1."):
            run_option_1_menu(fzf)
        else:
            print("Exiting...")
            return


def ensure_dir(path: str):
    if os.path.exists(path):
        return
    os.makedirs(path)


def ensure_essential_folders():
    for rel_path in ESSENTIAL_FOLDERS:
        ensure_dir(os.path.join(script_dir, rel_path))


def run_option_1_menu(fzf: pyfzf.FzfPrompt):
    submenu = [
        "1-1. Create modded BNKs",
        "1-2. Extract BNKs (audio + names from CVS)",
        "1-3. Extract BNKs (name-only from CVS)",
        "Back",
    ]
    choice = fzf.prompt(submenu, "--cycle --layout reverse")
    if not choice or choice[0] == "Back":
        return
    if choice[0].startswith("1-1"):
        create_modded_bnks()
    elif choice[0].startswith("1-2"):
        extract_bnks(name_only=False)
    elif choice[0].startswith("1-3"):
        extract_bnks(name_only=True)


def run_wwiseutil(
    filepath: str = None,
    output: str = None,
    replace: bool = False,
    target: str = None,
    unpack: bool = False,
) -> bool:
    wwiseutil_path = None
    if os.name == "nt":  # Windows
        wwiseutil_path = os.path.join(tools_folder, "wwiseutil.exe")
    if os.name == "posix":  # macOS/Linux
        wwiseutil_path = os.path.join(tools_folder, "wwiseutil")  # TODO: CHANGE ASAP
    if not os.path.isfile(wwiseutil_path):
        print(f"Error: wwiseutil not found at {wwiseutil_path}")
        return False
    log = subprocess.run(
        [
            wwiseutil_path,
            "-f",
            filepath,
            "-o",
            output,
            "-t",
            target,
            "-r" if replace else "",
            "-u" if unpack else "",
            "-v",
        ],
        capture_output=True,
        text=True,
    )
    with open("output.log", "w") as log_file:
        log_file.write(log.stdout)
        log_file.write(log.stderr)
    if log.returncode != 0:
        print(f"Error running wwiseutil: {log.stderr}")
        return False
    return True


def run_bnktool(
    bnk_input: str,
    bnk_output: str = None,
    wem_output: str = None,
    extract: bool = False,
    pack: bool = False,
) -> bool:
    bnktool_path = None
    if os.name == "nt":  # Windows
        bnktool_path = os.path.join(tools_folder, "BNKTool", "BNKTool.exe")
    if os.name == "posix":  # macOS/Linux
        bnktool_path = os.path.join(
            tools_folder, "BNKTool", "BNKTool"
        )  # TODO: CHANGE ASAP
    if not os.path.isfile(bnktool_path):
        print(f"Error: bnktool not found at {bnktool_path}")
        return False
    if extract and not wem_output:
        print("Error: extract mode requires wem_output.")
        return False
    if pack and (not wem_output or not bnk_output):
        print("Error: pack mode requires wem_output and bnk_output.")
        return False
    args = [bnktool_path]
    if extract:
        args += ["-bi", bnk_input, "-wo", wem_output, "-e", "-s"]
    elif pack:
        args += ["-bi", bnk_input, "-wo", wem_output, "-bo", bnk_output, "-p", "-s"]
    else:
        print("Error: Must specify either extract or pack mode.")
        return False
    log = subprocess.run(args, capture_output=True, text=True)
    with open("bnktool_output.log", "w") as log_file:
        log_file.write(log.stdout)
        log_file.write(log.stderr)
    if log.returncode != 0:
        print(f"Error running bnktool: {log.stderr}")
        return False
    return True


def collect_files_with_ext(root: str, ext: str) -> list[str]:
    found = []
    for path_root, _, files in os.walk(root):
        for file_name in files:
            if file_name.lower().endswith(ext.lower()):
                found.append(os.path.join(path_root, file_name))
    return found


def safe_move(src: str, dst_dir: str):
    ensure_dir(dst_dir)
    dst = os.path.join(dst_dir, os.path.basename(src))
    stem, ext = os.path.splitext(os.path.basename(src))
    i = 1
    while os.path.exists(dst):
        dst = os.path.join(dst_dir, f"{stem}_{i}{ext}")
        i += 1
    shutil.move(src, dst)
    return dst


def parse_wem_numeric_id(file_name: str):
    match = re.match(r"^([0-9a-fA-F]+)(?:-.*)?\.wem$", file_name, flags=re.IGNORECASE)
    if not match:
        return None
    return convert_hex_to_dec(match.group(1))


def build_cvs_wem_index():
    index = defaultdict(list)
    if not os.path.isdir(cvs_renamed_wem_folder):
        return index
    for file_path in collect_files_with_ext(cvs_renamed_wem_folder, ".wem"):
        base = os.path.basename(file_path)
        match = re.match(r"^(\d+)(?:-.*)?\.wem$", base, flags=re.IGNORECASE)
        if match:
            index[int(match.group(1))].append(file_path)
    return index


def choose_best_name(candidates: list[str]) -> str:
    longest = max(candidates, key=lambda p: len(os.path.splitext(os.path.basename(p))[0]))
    longest_len = len(os.path.splitext(os.path.basename(longest))[0])
    tied = [p for p in candidates if len(os.path.splitext(os.path.basename(p))[0]) == longest_len]
    for item in tied:
        if "English(US)" in item:
            return os.path.basename(item)
    return os.path.basename(longest)


def get_bank_streams_folder(extract_root: str):
    matches = list(Path(extract_root).rglob("bank_streams"))
    if matches:
        return str(matches[0])
    return None


def rename_streams_to_wem(extract_root: str):
    for file_path in Path(extract_root).rglob("*.stream"):
        file_path.rename(file_path.with_suffix(".wem"))


def normalize_bank_stream_ids(bank_streams: str):
    for wem_path in Path(bank_streams).glob("*.wem"):
        stem = wem_path.stem
        dec = convert_hex_to_dec(stem)
        if dec is None:
            continue
        target = wem_path.with_name(f"{dec}.wem")
        if target == wem_path:
            continue
        if target.exists():
            if target.stat().st_size >= wem_path.stat().st_size:
                wem_path.unlink()
            else:
                target.unlink()
                wem_path.rename(target)
        else:
            wem_path.rename(target)


def apply_cvs_replacements(bank_streams: str, replace_audio: bool):
    cvs_index = build_cvs_wem_index()
    if not cvs_index:
        print(f"Warning: no CVS WEM folder found at '{cvs_renamed_wem_folder}'.")
        return
    for wem_file in Path(bank_streams).glob("*.wem"):
        if not wem_file.stem.isdigit():
            continue
        wem_id = int(wem_file.stem)
        candidates = cvs_index.get(wem_id)
        if not candidates:
            continue
        if replace_audio:
            biggest = max(candidates, key=lambda p: os.path.getsize(p))
            shutil.copy2(biggest, str(wem_file))
        desired_name = choose_best_name(candidates)
        desired_path = wem_file.with_name(desired_name)
        if desired_path != wem_file and not desired_path.exists():
            wem_file.rename(desired_path)


def prepare_custom_wems_for_modding():
    sanitize_input_filenames(output_wem_folder)
    wem_files = collect_files_with_ext(output_wem_folder, ".wem")
    by_id = defaultdict(list)
    for wem in wem_files:
        parsed = parse_wem_numeric_id(os.path.basename(wem))
        if parsed is None:
            moved_to = safe_move(wem, os.path.join(script_dir, invalid_name_folder))
            print(f"Moved invalid filename to '{moved_to}'")
            continue
        by_id[parsed].append(wem)

    best_by_id = {}
    for wem_id, files in by_id.items():
        best = max(files, key=os.path.getsize)
        best_by_id[wem_id] = best
        for item in files:
            if item == best:
                continue
            moved_to = safe_move(item, os.path.join(script_dir, dupe_id_folder))
            print(f"Moved duplicate ID file to '{moved_to}'")

    staging = os.path.join(script_dir, extras_folder, "0-TEMP", "normalized-custom-wems")
    if os.path.exists(staging):
        shutil.rmtree(staging)
    ensure_dir(staging)
    for wem_id, source_file in best_by_id.items():
        shutil.copy2(source_file, os.path.join(staging, f"{wem_id}.wem"))
    return staging, set(best_by_id.keys())


def sanitize_input_filenames(input_folder_path: str) -> list[str]:
    renamed_log: list[str] = []
    for root, _, files in os.walk(input_folder_path):
        for file_name in files:
            base_name, ext = os.path.splitext(file_name)
            if ext.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
                continue

            clean_base = re.sub(r"[\[\](){} ]", "", base_name)
            clean_base = re.sub(r"[^a-zA-Z0-9_-]", "-", clean_base)
            clean_base = re.sub(r"-+", "-", clean_base).strip("-")
            new_base = clean_base if clean_base else "audio-cleaned"
            new_name = f"{new_base}{ext}"

            if new_name == file_name:
                continue

            src_path = os.path.join(root, file_name)
            final_name = new_name
            final_path = os.path.join(root, final_name)
            counter = 1

            while os.path.exists(final_path):
                final_name = f"{new_base}_{counter}{ext}"
                final_path = os.path.join(root, final_name)
                counter += 1

            try:
                os.rename(src_path, final_path)
                renamed_log.append(f"Renamed: '{file_name}' -> '{final_name}'")
                print(f"  Sanitized: {file_name} -> {final_name}")
                time.sleep(0.1)
            except OSError as exc:
                print(f"Failed to rename '{file_name}': {exc}")

    return renamed_log


def delete_soundbanks_file():
    try:
        os.remove(os.path.join(tools_folder, "soundbanks.txt"))
    except:
        print("Failed to delete soundbanks.txt, it may not exist yet. Continuing...")


def convert_wav_to_wem() -> bool:
    volume_input = None
    while not volume_input:
        volume_input = input(
            "Enter volume multiplier (0.1 to 5.0, e.g. 0.5 = half, 1.0 = original, 2.0 = double) [default: 1.0]  or Q to cancel"
        )
        if not volume_input:
            volume_input = "1.0"
        if volume_input.upper() == "Q":
            return False
        try:
            volume_input = float(volume_input)
            if not (0.1 <= volume_input <= 5.0):
                print("Volume multiplier must be between 0.1 and 5.0.")
                volume_input = None
        except ValueError:
            print("Invalid input. Please enter a number or 'Q'.")
            volume_input = None
    print(f"Using volume multiplier: {volume_input}")

    ffmpeg_path = (
        os.path.join(tools_folder, "ffmpeg.exe") if os.name == "nt" else "ffmpeg"
    )
    ffprobe_path = (
        os.path.join(tools_folder, "ffprobe.exe") if os.name == "nt" else "ffprobe"
    )
    vgmstream_path = os.path.join(
        vgm_sub_folder, "vgmstream-cli" + (".exe" if os.name == "nt" else "")
    )
    ffprobe_found = False
    if os.name == "nt" and not os.path.isfile(ffmpeg_path):
        print(f"Error: ffmpeg not found at {ffmpeg_path}")
        return False
    if os.name == "nt" and not os.path.isfile(ffprobe_path):
        print(f"Warning: ffprobe not found at {ffprobe_path}")
        ffprobe_found = False
    if not os.path.isfile(vgmstream_path):
        print(f"Error: vgmstream-cli not found at {vgmstream_path}")
        return False
    if os.name == "posix" and not shutil.which("ffmpeg"):
        print("Error: ffmpeg not found in PATH")
        return False
    if os.name == "posix" and not shutil.which("ffprobe"):
        print("Warning: ffprobe not found in PATH")
        ffprobe_found = False
    else:
        ffprobe_found = True

    if not os.path.isdir(input_wav_folder) or not os.path.isdir(output_wem_folder):
        print("Error: Input or output folder does not exist.")
        return False

    files = []
    for root, dirs, filenames in os.walk(input_wav_folder, onerror=lambda e: None):
        for name in filenames:
            _, ext = os.path.splitext(name)
            if ext.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                files.append(os.path.join(root, name))

    renamed_log = sanitize_input_filenames(input_wav_folder)
    sanitized_count = len(renamed_log)
    if sanitized_count > 0:
        print(f"Sanitized {sanitized_count} filenames.")
    else:
        print("No filename sanitization needed.")

    files = []
    for root, dirs, filenames in os.walk(input_wav_folder, onerror=lambda e: None):
        for name in filenames:
            _, ext = os.path.splitext(name)
            if ext.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                files.append(os.path.join(root, name))

    temp_folder = os.path.join(extras_folder, "0-TEMP")

    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
    os.makedirs(temp_folder)
    processed_files = []
    success_count = 0
    for file in files:
        rel_path = os.path.relpath(file, input_wav_folder)
        rel_temp_folder = os.path.join(temp_folder, os.path.dirname(rel_path))
        amped_wav_path = os.path.join(
            rel_temp_folder, os.path.basename(file.split(".")[0] + ".wav")
        )
        temp_decode_path = os.path.join(
            rel_temp_folder, os.path.basename(file.split(".")[0] + "_decoded.wav")
        )

        channels = 1
        target_rate = 48000

        if file.split(".")[-1].lower() == "wem":
            decode_cmd = [vgmstream_path, file, "-o", temp_decode_path]
            try:
                subprocess.run(decode_cmd, check=True, capture_output=True)
                print(f"Decoded WEM: {file} -> {temp_decode_path}")
                source_file = temp_decode_path
            except subprocess.CalledProcessError as e:
                print(f"Error decoding {file}: {e.stderr.decode()}")
                continue
            if not ffprobe_found:
                print(f"Skipping {file} due to missing ffprobe for format analysis.")
                continue
            probe_cmd = [
                ffprobe_path,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=channels,sample_rate",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                temp_decode_path,
            ]
            try:
                probe_result = subprocess.run(
                    probe_cmd, check=True, capture_output=True, text=True
                )
                channels, sample_rate = map(
                    int, probe_result.stdout.strip().split("\n")
                )
                print(f"Probed {file}: channels={channels}, sample_rate={target_rate}")
                if channels not in {1, 2}:
                    print(
                        f"Unsupported channel count ({channels}) in {file}. Setting to 1"
                    )
                    channels = 1
            except subprocess.CalledProcessError as e:
                print(f"Error probing {file}: {e.stderr.decode()}")
                channels = 1
                target_rate = 48000

        elif file.split(".")[-1].lower() in {"mp3", "ogg", "m4a", "flac", "wav"}:
            if not ffprobe_found:
                print(f"Skipping {file} due to missing ffprobe for format analysis.")
                continue
            probe_cmd = [
                ffprobe_path,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=channels",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                file,
            ]
            try:
                probe_result = subprocess.run(
                    probe_cmd, check=True, capture_output=True, text=True
                )
                channels = int(probe_result.stdout.strip().replace("\n", ""))
                print(f"Probed {file}: channels={channels}, sample_rate={target_rate}")
                if channels not in {1, 2}:
                    print(
                        f"Unsupported channel count ({channels}) in {file}. Setting to 1"
                    )
                    channels = 1
            except subprocess.CalledProcessError as e:
                print(f"Error probing {file}: {e.stderr.decode()}")
                channels = 1
                target_rate = 48000

        print(
            f"Processing: {file} with channels={channels}, sample_rate={target_rate} (forced)"
        )
        input_file = temp_decode_path if file.split(".")[-1].lower() == "wem" else file

        ffmpeg_args = [
            "-vn",  # Ignore any video streams (harmless)
            "-i",
            str(input_file),
            "-filter:a",
            f"volume={volume_input}",
            "-ar",
            str(target_rate),
            "-ac",
            str(channels),
            "-c:a",
            "pcm_s16le",
            "-f",
            "wav",
            "-y",
            amped_wav_path,
        ]

        ffmpeg_output = subprocess.run(
            [ffmpeg_path] + ffmpeg_args, capture_output=True, text=True
        )

        if file.split(".")[-1].lower() == "wem" and os.path.exists(temp_decode_path):
            os.remove(temp_decode_path)

        if ffmpeg_output.returncode != 0:
            print(f"Error processing {file} with ffmpeg: {ffmpeg_output.stderr}")
            print("FFmpeg output:", ffmpeg_output.stdout)
        else:
            print(f"Amplified {file}")
            processed_files.append(
                {
                    "original_file": file,
                    "amped_wav": amped_wav_path,
                    "channels": channels,
                }
            )
            success_count += 1
    if success_count > 0:
        print(f"Successfully processed {success_count} files.")
    else:
        print("No files were processed successfully.")
        return

    wem_count = 0
    for item in processed_files:
        wav_file = item["amped_wav"]
        channels = item["channels"]
        base_name = os.path.basename(os.path.basename(item["original_file"]))

        rel_path = os.path.relpath(item["original_file"], start=input_wav_folder)
        out_dir = os.path.join(output_wem_folder, os.path.dirname(rel_path))

        os.makedirs(out_dir, exist_ok=True)

        wem_path = os.path.join(out_dir, os.path.splitext(base_name)[0] + ".wem")
        # try:
        amp_bytes = open(wav_file, "rb").read()
        if len(amp_bytes) < 44:
            print(f"File too short to be a valid WAV: {wav_file}")
            continue
        data_index = amp_bytes.find(b"data") + 8  # "data" chunk
        if data_index < 8:
            print(f"Could not find 'data' chunk in WAV: {wav_file}")
            continue
        data_size = struct.unpack_from("<I", amp_bytes, data_index - 4)[
            0
        ]  # UInt32 little-endian
        pcm = amp_bytes[
            data_index : data_index + data_size
        ]  # slice of length data_size
        file_size = 68 + data_size if channels == 1 else 88 + data_size
        header = MONO_HEADER if channels == 1 else STEREO_HEADER
        new_header = (
            header[:4]
            + struct.pack("<I", file_size - 8)
            + header[8:]
            + b"data"
            + struct.pack("<I", data_size)
        )
        with open(wem_path, "wb") as wem_file:
            wem_file.write(new_header)
            wem_file.write(pcm)
        print(f"Converted to WEM ({'mono' if channels == 1 else 'stereo'}): {wem_path}")
        wem_count += 1

        # except Exception as e:
        #     print(f"Error reading WAV file {wav_file}: {e}")
        #     continue
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)

    print("======================================")
    if wem_count > 0:
        print(f"Successfully converted {wem_count} files to WEM format.")
    print(f"Total files processed: {len(processed_files)}")
    print(f"Output WEM files: {wem_count}")
    print("Amplification level:", volume_input)
    print("======================================")
    input("Press Enter to continue...")
    return True


def extract_bnks(name_only: bool = False):
    ensure_essential_folders()
    bnk_files = collect_files_with_ext(original_bnk_folder, ".bnk")
    if not bnk_files:
        print(f"No BNK files found in '{original_bnk_folder}'.")
        return False

    ensure_dir(extracted_bnk_folder)
    success = 0
    for bnk_file in bnk_files:
        bnk_name = Path(bnk_file).stem
        temp_root = os.path.join(script_dir, extras_folder, "0-TEMP", "extract", bnk_name)
        if os.path.exists(temp_root):
            shutil.rmtree(temp_root)
        ensure_dir(temp_root)

        if not run_bnktool(bnk_input=bnk_file, wem_output=temp_root, extract=True):
            print(f"Failed extracting '{bnk_file}'")
            continue

        rename_streams_to_wem(temp_root)
        bank_streams = get_bank_streams_folder(temp_root)
        if bank_streams:
            normalize_bank_stream_ids(bank_streams)
            apply_cvs_replacements(bank_streams, replace_audio=not name_only)

        target_folder = os.path.join(script_dir, extracted_bnk_folder, bnk_name)
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder)
        shutil.copytree(temp_root, target_folder)
        print(f"Extracted '{bnk_file}' -> '{target_folder}'")
        success += 1

    print(f"Completed extraction for {success}/{len(bnk_files)} BNK files.")
    return success > 0


def process_test_files():
    pass
    # TODO: Low priority


def isolate_custom_wems():
    pass
    # TODO: Low priority


def process_bnk_files(bnk_files: list[str] = None, output_folder: str = None):
    return extract_bnks(name_only=False)


def create_modded_bnks():
    ensure_essential_folders()
    ensure_dir(modded_bnk_output)
    bnk_files = collect_files_with_ext(original_bnk_folder, ".bnk")
    if not bnk_files:
        print(f"No BNK files found in '{original_bnk_folder}'.")
        return False

    custom_wems = collect_files_with_ext(output_wem_folder, ".wem")
    if not custom_wems:
        print(f"No WEM files found in '{output_wem_folder}'.")
        return False

    total_size_mb = round(sum(os.path.getsize(w) for w in custom_wems) / (1024 * 1024), 2)
    if total_size_mb > 580:
        print(f"Error: custom WEM size is {total_size_mb} MB (limit is 580 MB).")
        return False

    staging_wems, normalized_ids = prepare_custom_wems_for_modding()
    staged_files = collect_files_with_ext(staging_wems, ".wem")
    if not staged_files:
        print("No valid WEM files remain after sanitization.")
        return False

    matched_ids = set()
    packed_ok = 0
    for bnk_file in bnk_files:
        bnk_name = Path(bnk_file).stem
        temp_root = os.path.join(script_dir, extras_folder, "0-TEMP", "pack", bnk_name)
        if os.path.exists(temp_root):
            shutil.rmtree(temp_root)
        ensure_dir(temp_root)

        if not run_bnktool(bnk_input=bnk_file, wem_output=temp_root, extract=True):
            print(f"Failed extracting '{bnk_file}'")
            continue

        rename_streams_to_wem(temp_root)
        bank_streams = get_bank_streams_folder(temp_root)
        if not bank_streams:
            print(f"No 'bank_streams' found for '{bnk_file}'")
            continue
        normalize_bank_stream_ids(bank_streams)

        bank_files = {p.name for p in Path(bank_streams).glob("*.wem")}
        replaced = 0
        for staged in staged_files:
            wem_id = int(Path(staged).stem)
            target = os.path.join(bank_streams, f"{wem_id}.wem")
            if f"{wem_id}.wem" in bank_files:
                shutil.copy2(staged, target)
                matched_ids.add(wem_id)
                replaced += 1

        output_bnk = os.path.join(modded_bnk_output, os.path.basename(bnk_file))
        if not run_bnktool(
            bnk_input=bnk_file,
            bnk_output=output_bnk,
            wem_output=temp_root,
            pack=True,
        ):
            print(f"Failed repacking '{bnk_file}'")
            continue
        print(f"Packed '{output_bnk}' with {replaced} replaced WEM(s)")
        packed_ok += 1

    for wem_id in sorted(normalized_ids - matched_ids):
        source = os.path.join(staging_wems, f"{wem_id}.wem")
        if os.path.exists(source):
            moved = safe_move(source, os.path.join(script_dir, no_match_folder))
            print(f"No BNK match for ID {wem_id}; moved to '{moved}'")

    print(f"Created {packed_ok}/{len(bnk_files)} modded BNK files.")
    return packed_ok > 0


def get_audio_id_list():
    pass


def amplify_audio_files():
    pass


def remove_filename_suffix():
    pass


def copy_bnks_and_run_rpk():
    pass


def convert_wem_to_wav():
    pass


def find_audio_id_and_index(bnk_file: Path, endian: str = "<"):
    """
    Returns a list of (index, audio_id) tuples from the DIDX section.
    """
    with open(bnk_file, "rb") as f:
        # scan sections until we hit DIDX (or stop)
        while True:
            magic = f.read(4)
            if len(magic) < 4:
                raise ValueError("Reached EOF without finding DIDX")

            magic = magic.decode("ascii", errors="ignore")
            size_bytes = f.read(4)
            if len(size_bytes) < 4:
                raise ValueError("Truncated section header")

            size = struct.unpack(f"{endian}I", size_bytes)[0]
            data = f.read(size)
            if len(data) < size:
                raise ValueError("Truncated section data")

            if magic == "DIDX":
                didx_data = data
                break

    if len(didx_data) % 12 != 0:
        raise ValueError("DIDX size is not a multiple of 12 bytes")

    entries = []
    entry_count = len(didx_data) // 12
    for i in range(entry_count):
        off = i * 12
        audio_id, file_offset, file_size = struct.unpack(
            f"{endian}III", didx_data[off : off + 12]
        )
        entries.append(audio_id)

    return entries


def convert_hex_to_dec(hex_string: str) -> int:
    try:
        if re.match(r"^[0-9a-fA-F]+$", hex_string) and re.match(
            r"[a-fA-F]", hex_string
        ):
            return int(hex_string, 16)
        elif re.match(r"^\d+$", hex_string):
            return int(hex_string)
        else:
            raise ValueError("Input is not a valid hexadecimal or decimal number.")
    except ValueError as e:
        print(f"Error converting '{hex_string}': {e}")
        return None


if __name__ == "__main__":
    main()
