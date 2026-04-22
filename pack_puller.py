# Script to pull pack data
import os
import pandas as pd
import subprocess
from tqdm import tqdm
from pathlib import Path

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
    
    os.makedirs(downloads_dir, exist_ok=True)

    path = os.path.join(downloads_dir, pack_slug)

    if(os.path.isdir(path)):
        tqdm.write(f"Pack {pack_slug} already exists, skipping...")
        return

    tqdm.write(f"Installing {pack_slug} to {path}...")
    os.makedirs(path, exist_ok=True)

    subprocess.run(
        ["mrpack-install", pack_slug],
        capture_output=True,
        cwd=path
    )


if __name__ == "__main__":
    pull_packs_fs()
