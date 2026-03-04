import os
import subprocess
import shutil
import struct
import time
from pathlib import Path
import pyfzf
import re

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
bnk_extract_output = "4-Your-EXTRACTED-BNKs-Are-Here"
character_id_list_file = os.path.join(
    extras_folder, "0-CVS", "1_XTRA", "CHARACTER-ID-LIST.txt"
)

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
invalid_name_folder = os.path.join(script_dir, "x203-INVALID-NAME-Wems-Here")
audio_id_list_file = os.path.join(extras_folder, "AUDIO-ID-LIST.txt")

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
    extras_folder,
    ignore_folder,
    tools_folder,
    vgm_sub_folder,
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
    fzf = pyfzf.FzfPrompt()
    options = [
        "0. Convert custom audio files to WEM format",
        "1. Create a modded .bnk",
        "2. Extract .bnk",
        "3. Update .wem IDs",
        "4. Quit",
    ]
    options_prompt = fzf.prompt(options, "--cycle --layout reverse")
    if not options_prompt or options_prompt[0] == "4. Quit":
        print("Exiting...")
        return
    selected_option = options_prompt[0][0]  # Get the first character
    if selected_option == "0":
        convert_wav_to_wem()
    elif selected_option == "1":
        create_modded_bnks()
    elif selected_option == "2":
        extract_bnks()
    elif selected_option == "3":
        get_audio_id_list()
    else:
        print("Invalid option. Exiting...")


def ensure_dir(path: str):
    if os.path.exists(path):
        return
    os.makedirs(path)


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
    bnk_output: str,
    wem_output: str,
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

    renamed_log = []
    for file in files:
        renamed_log = sanitize_input_filenames(file)
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


def extract_bnks():
    print("Operation 2: Extracting .wem files from vanilla .bnk files...")
    ensure_dir(tools_folder)
    ensure_dir(bnk_extract_output)

    bnk_files = [
        os.path.join(original_bnk_folder, file)
        for file in os.listdir(original_bnk_folder)
        if file.lower().endswith(".bnk")
    ]
    if not bnk_files:
        print(
            f"No BNK files found in {original_bnk_folder}. Please add BNK files to process."
        )
        return

    sound_banks_file = os.path.join(tools_folder, "sound_banks.txt")
    for stale in (sound_banks_file, os.path.join(tools_folder, "soundbanks.txt")):
        if os.path.exists(stale):
            os.remove(stale)

    with open(sound_banks_file, "w", encoding="utf-8") as fp:
        for bnk_file in bnk_files:
            bnk_name = os.path.basename(bnk_file)
            fp.write(f"{os.path.splitext(bnk_name)[0]}\n")
            shutil.copy2(bnk_file, os.path.join(tools_folder, bnk_name))
            print(f"Copied {bnk_name} to '{tools_folder}'")

            folder_to_delete = os.path.join(tools_folder, os.path.splitext(bnk_name)[0])
            if os.path.isdir(folder_to_delete):
                shutil.rmtree(folder_to_delete)
                print(f"Deleted stale extraction folder: '{folder_to_delete}'")

    bnktool_output = run_bnktool(
        tools_folder, modded_bnk_output, tools_folder, extract=True
    )
    if not bnktool_output:
        print("Failed to extract BNK files.")
        return
    print(f"Successfully extracted BNK files to {tools_folder}")

    for folder in Path(tools_folder).iterdir():
        if not folder.is_dir():
            continue
        for stream_file in folder.rglob("*.stream"):
            wem_path = stream_file.with_suffix(".wem")
            stream_file.rename(wem_path)
            print(f"Renamed {stream_file.name} -> {wem_path.name}")

    bank_streams_folders = [
        folder
        for folder in Path(tools_folder).rglob("*")
        if folder.is_dir() and folder.name == "bank_streams"
    ]
    for bank_streams in bank_streams_folders:
        for wem_file in bank_streams.glob("*.wem"):
            base = wem_file.stem
            if not re.fullmatch(r"[a-fA-F0-9]+", base):
                continue
            if re.fullmatch(r"[0-9]+", base):
                print(
                    f"Skipping {wem_file.name} in {bank_streams} due to non-hexadecimal name"
                )
                continue
            try:
                decimal = str(int(base, 16))
                new_path = bank_streams / f"{decimal}.wem"
                wem_file.rename(new_path)
                print(f"Renamed {base}.wem -> {decimal}.wem")
            except ValueError as exc:
                print(f"Failed to convert {wem_file.name}: {exc}")

    for folder in Path(tools_folder).iterdir():
        if not folder.is_dir():
            continue
        if folder.name in {"Output", modded_bnk_output, "BNKTool"}:
            continue
        dest = Path(bnk_extract_output) / folder.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(folder), str(dest))
        print(f"Moved: {folder.name}")

    for file in Path(tools_folder).iterdir():
        if file.is_file() and (
            file.suffix.lower() in {".wem", ".bnk"}
            or file.name in {"sound_banks.txt", "soundbanks.txt"}
        ):
            file.unlink()
            print(f"Deleted {file.name} from '{tools_folder}'")

    for folder in Path(tools_folder).iterdir():
        if folder.is_dir() and folder.name not in {
            "Output",
            modded_bnk_output,
            "BNKTool",
        }:
            shutil.rmtree(folder)
            print(f"Deleted folder: '{folder.name}' from '{tools_folder}'")

    operation_11_smart_replace_and_organize(
        extracted_folder=bnk_extract_output, bnk_files=bnk_files
    )
    rename_extracted_folders_with_character_ids(bnk_extract_output)
    print("Operation 2 completed.")


def rename_extracted_folders_with_character_ids(extracted_folder: str):
    print("Renaming extracted folders with CHARACTER-ID-LIST mappings...")
    char_id_map = load_character_id_list()
    if not char_id_map:
        print("No character mappings loaded. Skipping friendly rename.")
        return

    root = Path(extracted_folder)
    if not root.is_dir():
        return

    for folder in [entry for entry in root.iterdir() if entry.is_dir()]:
        original_name = folder.name

        if re.search(r"_Old\d+$", original_name):
            continue

        already_prefixed = any(
            original_name.startswith(f"{char_name}-")
            for char_name in char_id_map.values()
        )
        if already_prefixed:
            continue

        desired_name = original_name
        id_match = re.search(r"(\d{7})", original_name)
        if id_match:
            folder_id = id_match.group(1)
            if folder_id in char_id_map:
                desired_name = f"{char_id_map[folder_id]}-{original_name}"

        desired_path = root / desired_name
        if desired_path.exists() and desired_path != folder:
            counter = 1
            archive_path = root / f"{desired_name}_Old{counter}"
            while archive_path.exists():
                counter += 1
                archive_path = root / f"{desired_name}_Old{counter}"
            desired_path.rename(archive_path)
            print(f"Archived conflicting folder: {desired_name} -> {archive_path.name}")

        if desired_name != original_name:
            folder.rename(root / desired_name)
            print(f"Renamed: {original_name} -> {desired_name}")


def operation_11_smart_replace_and_organize(
    extracted_folder: str, bnk_files: list[str] = None
) -> dict[str, int]:
    print("Operation 11: Smart replacing and organizing .wem files...")

    base_wems_folder = os.path.join(extras_folder, "0-CVS", "2-RENAMED-WEMs-Are-Here")
    if not os.path.isdir(base_wems_folder):
        print(f"Error: '{base_wems_folder}' not found. Skipping replacement.")
        return {"replaced": 0, "renamed": 0, "skipped": 0, "moved": 0}

    if bnk_files:
        bnk_stems = {
            os.path.splitext(os.path.basename(bnk_file))[0] for bnk_file in bnk_files
        }
    else:
        bnk_stems = {
            os.path.splitext(file)[0]
            for file in os.listdir(original_bnk_folder)
            if file.lower().endswith(".bnk")
        }

    if not os.path.isdir(extracted_folder):
        print(f"Extracted folder not found: {extracted_folder}")
        return {"replaced": 0, "renamed": 0, "skipped": 0, "moved": 0}

    bnk_folders = [
        entry
        for entry in Path(extracted_folder).iterdir()
        if entry.is_dir() and entry.name in bnk_stems
    ]

    wem_index: dict[str, list[Path]] = {}
    for wem_file in Path(base_wems_folder).rglob("*.wem"):
        match = re.match(r"^(\d+)(?:-.*)?$", wem_file.stem)
        if not match:
            continue
        wem_id = match.group(1)
        wem_index.setdefault(wem_id, []).append(wem_file)

    replaced_count = 0
    renamed_count = 0
    skipped_count = 0
    moved_count = 0

    for bnk_folder in bnk_folders:
        bank_streams = bnk_folder / "bank_streams"
        if not bank_streams.is_dir():
            continue

        wem_files = [
            wem for wem in bank_streams.glob("*.wem") if re.fullmatch(r"\d+", wem.stem)
        ]

        for wem in wem_files:
            wem_id = wem.stem
            candidates = wem_index.get(wem_id)
            if not candidates:
                skipped_count += 1
                print(f"Skipped (no match in CVS): {wem.name}")
                continue

            best_by_size = max(
                candidates, key=lambda candidate: candidate.stat().st_size
            )
            shutil.copy2(best_by_size, wem)
            replaced_count += 1
            print(
                f"Replaced content of {wem.name} <- {best_by_size.name} "
                f"({best_by_size.stat().st_size} bytes)"
            )

            longest_name_candidate = max(
                candidates, key=lambda candidate: len(candidate.stem)
            )
            en_us_candidates = [
                candidate
                for candidate in candidates
                if "English(US)" in str(candidate.parent)
                and len(candidate.stem) == len(longest_name_candidate.stem)
            ]
            if en_us_candidates and "English(US)" not in str(
                longest_name_candidate.parent
            ):
                longest_name_candidate = en_us_candidates[0]

            desired_name = longest_name_candidate.name
            desired_path = bank_streams / desired_name
            if desired_name != wem.name and not desired_path.exists():
                wem.rename(desired_path)
                renamed_count += 1
                print(f"Renamed: {wem.name} -> {desired_name} (longest name)")
            elif desired_name != wem.name:
                print(f"Skipped rename {wem.name} -> {desired_name} (name conflict)")

        all_wems = list(bank_streams.rglob("*.wem"))
        for wem in all_wems:
            parts = wem.stem.split("_")
            sub_folder = parts[2] if len(parts) >= 3 else "Unknown"
            sub_path = bank_streams / sub_folder
            sub_path.mkdir(parents=True, exist_ok=True)

            dest = sub_path / wem.name
            if wem.resolve() == dest.resolve():
                continue

            if dest.exists():
                dest.unlink()
            shutil.move(str(wem), str(dest))
            moved_count += 1
            print(f"Moved: {wem.name} -> {sub_folder}/")

    print("========================================")
    print("Operation 11 Summary (updated logic)")
    print("========================================")
    print(f"Replaced content (largest file): {replaced_count}")
    print(f"Renamed to longest name     : {renamed_count}")
    print(f"Skipped (no match/conflict) : {skipped_count}")
    print(f"Organized into subfolders   : {moved_count}")
    print("========================================")

    return {
        "replaced": replaced_count,
        "renamed": renamed_count,
        "skipped": skipped_count,
        "moved": moved_count,
    }


def load_character_id_list():
    character_id_map = {}
    if not os.path.isfile(character_id_list_file):
        return character_id_map
    with open(character_id_list_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^(\d{7})\s*:\s*(.+)$", line)
            if match:
                char_id = match.group(1)
                char_name = re.sub(r'[<>:"/\\|?*]', "_", match.group(2).strip())
                character_id_map[char_id] = char_name
                continue
            reverse_match = re.match(r"^(.+)\s*:\s*(\d{7})$", line)
            if reverse_match:
                char_name = re.sub(r'[<>:"/\\|?*]', "_", reverse_match.group(1).strip())
                char_id = reverse_match.group(2)
                character_id_map[char_id] = char_name
                continue
            print(f"Skipping invalid line in character ID list: {line}")
    return character_id_map


def process_test_files():
    pass
    # TODO: Low priority


def isolate_custom_wems():
    pass
    # TODO: Low priority


def process_bnk_files(bnk_files: list[str] = None, output_folder: str = None):
    pass


def create_modded_bnks():
    ensure_dir(tools_folder)
    bnk_files = []
    for root, _, files in os.walk(original_bnk_folder):
        for file in files:
            if file.lower().endswith(".bnk"):
                bnk_files.append(os.path.join(root, file))
    if not bnk_files:
        print(
            f"No BNK files found in {original_bnk_folder}. Please add BNK files to process."
        )
        return

    wem_files = []
    for root, _, files in os.walk(output_wem_folder):
        for file in files:
            if file.lower().endswith(".wem"):
                wem_files.append(os.path.join(root, file))
    if not wem_files:
        print(
            f"No WEM files found in {output_wem_folder}. Please convert WAV files to WEM first."
        )
        return

    sanitized_log = sanitize_input_filenames(output_wem_folder)

    if not os.listdir(output_wem_folder):
        print(
            "No valid WEM files found in output folder after sanitization. Please check your files."
        )
        return

    for file in os.listdir(output_wem_folder):
        decimal_id = convert_hex_to_dec(os.path.splitext(file)[0])
        if decimal_id is None:
            print(f"Skipping file with invalid name (not hex or decimal): {file}")
            continue
        else:
            print(f"File {file} has valid ID: {decimal_id}")
            os.rename(
                os.path.join(output_wem_folder, file),
                os.path.join(output_wem_folder, f"{decimal_id}.wem"),
            )
    sanitized_filenames = [
        f for f in os.listdir(output_wem_folder) if f.endswith(".wem")
    ]

    for bnk_file in bnk_files:
        bnk_output = modded_bnk_output
        bnk_input = original_bnk_folder
        wem_output = os.path.join(extras_folder, "0-TEMP")
        wem_input = output_wem_folder

        bnktool_output = run_bnktool(bnk_input, bnk_output, wem_output, extract=True)

        if not bnktool_output:
            print(f"Failed to extract WEMs from {bnk_file}. Skipping this BNK.")
            continue
        for file in sanitized_filenames:
            wem_path = os.path.join(output_wem_folder, file)
            try:
                wem_id = int(os.path.splitext(file)[0])
                print(f"Processing WEM: {file} with ID {wem_id}")
                vanilla_wems = os.listdir(
                    os.path.join(
                        wem_output,
                        os.path.basename(bnk_file).replace(".bnk", ""),
                        "bank_streams",
                    )
                )
                if f"{wem_id}.wem" in vanilla_wems:
                    print(
                        f"Found matching WEM ID {wem_id} in extracted BNK. Replacing with {file}."
                    )
                    shutil.copy(
                        wem_path,
                        os.path.join(
                            wem_output,
                            os.path.basename(bnk_file).replace(".bnk", ""),
                            "bank_streams",
                            f"{wem_id}.wem",
                        ),
                    )
            except Exception as e:
                print(f"Error processing WEM {file}: {e}")
                continue

        bnktool_output = run_bnktool(bnk_input, bnk_output, wem_output, pack=True)
        if not bnktool_output:
            print(f"Failed to pack WEMs into BNK for {bnk_file}. Skipping this BNK.")
            continue
        print(f"Successfully created modded BNK for {bnk_file}")
        return True
        # output_path = modded_bnk_output
        # entries = find_audio_id_and_index(bnk_file)
        # for wem in sanitized_filenames:
        #     wem_path = os.path.join(output_wem_folder, wem)
        #     try:
        #         wem_id = int(os.path.splitext(wem)[0])
        #         wem_index = (
        #             entries.index(wem_id) + 1
        #         )  # +1 because entries is 0-indexed but we want 1-indexed
        #         print(f"Found match for {wem_id} in {bnk_file} at index {wem_index}")
        #         shutil.copy(
        #             wem_path, os.path.join(output_wem_folder, str(wem_index) + ".wem")
        #         )
        #     except ValueError:
        #         print(f"No match for {wem} in {bnk_file}. Skipping this WEM.")
        #         continue
        # if run_wwiseutil(
        #     os.path.join(original_bnk_folder, os.path.basename(bnk_file)),
        #     os.path.join(modded_bnk_output, os.path.basename(bnk_file)),
        #     replace=True,
        #     target=output_wem_folder,
        #     unpack=False,
        # ):
        #     print(f"Successfully created modded BNK for {bnk_file}")
        #     return True
        # else:
        #     print(f"Failed to create modded BNK for {bnk_file}")
        #     return False


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
