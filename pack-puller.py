# Script to pull pack data
import os
import pandas as pd
import subprocess
from tqdm import tqdm
from pathlib import Path

CWD = Path.cwd()
INPUT_CSV = "clean_modpacks_small.csv"
# MUST BE ABSOLUTE PATH
DOWNLOADS_DIR = CWD / "modpacks"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

df = pd.read_csv(INPUT_CSV)

for _, row in tqdm(df.iterrows(), total=len(df), desc="Pulling packs"):
    project_slug = row["slug"]

    path = os.path.join(DOWNLOADS_DIR, project_slug)

    if(os.path.isdir(path)):
        tqdm.write(f"Pack {project_slug} already exists, skipping...")
        continue

    tqdm.write(f"Installing {project_slug} to {path}...")
    os.makedirs(path, exist_ok=True)    

    result = subprocess.run(
        ["mrpack-install", project_slug], 
        capture_output=True, 
        cwd=path
    )
