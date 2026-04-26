# Script to pull pack data
import os
import pandas as pd
import subprocess
from tqdm import tqdm
from pathlib import Path
from utils import *

INPUT_CSV = "clean_modpacks_small.csv"
DOWNLOADS_DIR = Path.cwd() / "modpacks"


def pull_packs_fs(input_csv=INPUT_CSV, downloads_dir=DOWNLOADS_DIR):
    df = pd.read_csv(input_csv)
    pull_packs(df, downloads_dir)
    

def pull_packs(df, downloads_dir=DOWNLOADS_DIR):

    os.makedirs(downloads_dir, exist_ok=True)

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Pulling packs"):
        project_slug = row["slug"]
        pull_pack(project_slug, downloads_dir)


def pull_pack(pack_slug, downloads_dir=DOWNLOADS_DIR):
    downloads_dir = Path(downloads_dir)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    modpack_path = downloads_dir / pack_slug
    mods_directory = modpack_path / "mc" / "mods"

    if mods_directory.is_dir():
        print_as_orecle(f"Pack {pack_slug} installed.")
        return modpack_path

    print_as_orecle(f"Installing {pack_slug} to {modpack_path}...")
    modpack_path.mkdir(parents=True, exist_ok=True)

    completed_process = subprocess.run(
        ["mrpack-install", pack_slug],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=modpack_path,
        check=False,
    )

    if completed_process.returncode != 0:
        stdout = completed_process.stdout.strip()
        stderr = completed_process.stderr.strip()
        raise RuntimeError(
            f"Failed to install pack {pack_slug}.\n"
            f"stdout:\n{stdout or '<empty>'}\n"
            f"stderr:\n{stderr or '<empty>'}"
        )

    if not mods_directory.is_dir():
        discovered_paths = [str(path.relative_to(modpack_path)) for path in sorted(modpack_path.rglob("*"))[:20]]
        raise RuntimeError(
            f"Pack {pack_slug} finished installing but did not create the expected mods directory at "
            f"\"{mods_directory}\". Found these paths instead: {discovered_paths}"
        )

    return modpack_path


if __name__ == "__main__":
    pull_packs_fs()
