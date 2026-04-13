# Script to pull modpacks
import requests
import json
import subprocess
import os
import sys
import pandas as pd

PAGE_SIZE = 500

page_num = 0
idx = 0

# Type safe declaration of the dataframe
df = pd.DataFrame({
    "slug": pd.Series(dtype="string"),
    "project_id": pd.Series(dtype="string"),
    "title": pd.Series(dtype="string"),
    "downloads": pd.Series(dtype="int64"),
    "categories": pd.Series(dtype="object"),
})

while True:

    sys.stdout.write(f"\rSearching page {page_num}")
    sys.stdout.flush()

    params = {
        "facets": '[["project_type:modpack"]]',
        "limit": PAGE_SIZE,
        "offset": page_num * PAGE_SIZE,
        "index": "downloads",
    }
    r = requests.get("https://api.modrinth.com/v2/search", params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    # Ran out of results
    if(len(data["hits"]) == 0):
        break

    for hit in data["hits"]:
        df.loc[idx] = [hit["slug"], hit["project_id"], hit["title"], hit["downloads"], hit["categories"]]
        idx += 1

    page_num += 1

df.to_csv("modpacks.csv", index=False)