# Script to pull modpacks
import ast
import requests
import sys
import pandas as pd

PAGE_SIZE = 500


def parse_game_version(version):
    """Return a sortable tuple for Minecraft versions."""
    if(pd.isna(version)):
        return ()

    parts = []
    for part in str(version).split("."):
        if(not part.isdigit()):
            break
        parts.append(int(part))

    return tuple(parts)


def parse_game_versions(game_versions):
    if(isinstance(game_versions, list)):
        return game_versions

    if(pd.isna(game_versions)):
        return []

    if(not isinstance(game_versions, str)):
        return []

    try:
        parsed_versions = ast.literal_eval(game_versions)
        if(isinstance(parsed_versions, list)):
            return parsed_versions
    except (ValueError, SyntaxError):
        pass

    return []


def get_highest_game_version(game_versions):
    parsed_versions = parse_game_versions(game_versions)
    sortable_versions = [
        version for version in parsed_versions
        if(len(parse_game_version(version)) > 0)
    ]

    if(len(sortable_versions) == 0):
        return ""

    return max(sortable_versions, key=parse_game_version)

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
        "game_versions": pd.Series(dtype="object"),
        "highest_game_version": pd.Series(dtype="string"),
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
            game_versions = hit.get("game_versions", hit.get("versions", []))
            highest_game_version = get_highest_game_version(game_versions)
            df.loc[idx] = [
                hit["slug"],
                hit["project_id"],
                hit["title"],
                hit["downloads"],
                hit["categories"],
                game_versions,
                highest_game_version,
            ]
            idx += 1

        page_num += 1

    if(filepath is not None):
        df.to_csv(filepath, index=False)

    return df

if(__name__ == "__main__"):
    download_pack_csv("modpacks.csv")
