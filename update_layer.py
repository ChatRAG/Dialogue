import os
import shutil
import zipfile
import subprocess
import boto3
from pathlib import Path

LAYER_NAME = "dialogue"
CUSTOM_LIB_PATHS = []
TEMP_LAYER_DIR = Path("./python")
ZIP_PATH = "layer.zip"
RUNTIME = ["python3.9"]
DESCRIPTION = "Auto-updated Lambda Layer"
REQUIREMENTS_FILE = "requirements.txt"


def install_dependencies():
    print("[*] Installing dependencies into python...")
    if TEMP_LAYER_DIR.exists():
        shutil.rmtree(TEMP_LAYER_DIR)
    TEMP_LAYER_DIR.mkdir(parents=True)

    # Step 1: Install pydantic and pydantic-core with --only-binary
    cmd1 = [
        "pip3", "install",
        "pydantic==2.11.5",
        "pydantic-core==2.33.2",
        "tiktoken",
        "--platform", "manylinux2014_x86_64",
        "--only-binary=:all:",
        "-t", str(TEMP_LAYER_DIR)
    ]

    # Step 2: Install other dependencies from requirements.txt
    cmd2 = [
        "pip3", "install",
        "-r", REQUIREMENTS_FILE,
        "-t", str(TEMP_LAYER_DIR)
    ]

    # Execute both commands
    subprocess.run(cmd1, check=True)
    subprocess.run(cmd2, check=True)
    print("[✓] Dependencies installed.")


def prepare_layer_directory():
    for custom_lib_path in CUSTOM_LIB_PATHS:
        if not custom_lib_path.exists():
            raise FileNotFoundError(f"[!] Source directory '{custom_lib_path}' does not exist.")

        print("[*] Copying layer content...")
        shutil.copytree(custom_lib_path, TEMP_LAYER_DIR / custom_lib_path.name)


def zip_layer():
    if Path(ZIP_PATH).exists():
        os.remove(ZIP_PATH)

    print("[*] Zipping layer content...")
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(TEMP_LAYER_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, ".")
                zipf.write(full_path, arcname=rel_path)
    print(f"[+] Created zip file: {ZIP_PATH}")


def publish_layer():
    client = boto3.client("lambda")
    with open(ZIP_PATH, "rb") as f:
        response = client.publish_layer_version(
            LayerName=LAYER_NAME,
            Description=DESCRIPTION,
            Content={"ZipFile": f.read()},
            CompatibleRuntimes=RUNTIME
        )
    print(f"[+] Published new version: {response['Version']}")
    print(f"[+] ARN: {response['LayerVersionArn']}")
    return response['Version']


def cleanup():
    print("[*] Cleaning up temporary files...")
    if TEMP_LAYER_DIR.exists():
        shutil.rmtree(TEMP_LAYER_DIR)
    if Path(ZIP_PATH).exists():
        os.remove(ZIP_PATH)
    print("[✓] Cleanup complete.")


def main():
    try:
        print("[*] Installing dependencies...")
        install_dependencies()

        print("[*] Preparing layer directory...")
        prepare_layer_directory()

        print("[*] Zipping layer...")
        zip_layer()

        print("[*] Publishing new layer version...")
        version = publish_layer()

        print("[✓] Done. Published layer version:", version)
    finally:
        cleanup()


if __name__ == "__main__":
    main()
