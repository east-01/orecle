# Script to pull modpacks
import requests
import sys
import pandas as pd

PAGE_SIZE = 500

def download_pack_csv(filepath=None, page_size=PAGE_SIZE, allow_cache=True):
    """ Downloads a CSV of modpacks from the Modrinth API. Returns a dataframe of the results. """

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
            "limit": page_size,
            "offset": page_num * page_size,
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

    if(filepath is not None):
        df.to_csv(filepath, index=False)

    return df

if(__name__ == "__main__"):
    download_pack_csv("modpacks.csv")