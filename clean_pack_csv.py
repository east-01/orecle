# Script to clean modpacks
import ast
import pandas as pd
from download_pack_csv import get_highest_game_version, parse_game_version, parse_game_versions

MAX_ACCEPTED_HITS = 100
MIN_DOWNLOADS = 3000
CSV_IN = "modpacks.csv"
CSV_OUT = "modpacks_clean.csv"
KEEP_CATEGORIES = {"kitchen-sink", "quests"}


def parse_categories(cats):
    if(isinstance(cats, list)):
        return cats

    if(pd.isna(cats)):
        return []

    if(not isinstance(cats, str)):
        return []

    try:
        parsed_cats = ast.literal_eval(cats)
        if(isinstance(parsed_cats, list)):
            return parsed_cats
    except (ValueError, SyntaxError):
        pass

    return []


def clean_pack_csv_fs(
    csv_in=CSV_IN,
    csv_out=CSV_OUT,
    max_accepted_hits=MAX_ACCEPTED_HITS,
    min_downloads=MIN_DOWNLOADS,
    keep_categories=KEEP_CATEGORIES,
    group_by_game_version=True,
):
    
    df = pd.read_csv(csv_in)

    clean_df = clean_pack_csv(
        df,
        max_accepted_hits=max_accepted_hits,
        min_downloads=min_downloads,
        keep_categories=keep_categories,
        group_by_game_version=group_by_game_version,
    )
    clean_df.to_csv(csv_out, index=False)

    return clean_df

def clean_pack_csv(
    df,
    max_accepted_hits=MAX_ACCEPTED_HITS,
    min_downloads=MIN_DOWNLOADS,
    keep_categories=KEEP_CATEGORIES,
    group_by_game_version=True,
):

    df = df.copy()
    df["downloads"] = pd.to_numeric(df["downloads"], errors="coerce").fillna(0).astype("int64")

    # Type safe declaration of the dataframe
    clean_df = pd.DataFrame({
        "slug": pd.Series(dtype="string"),
        "project_id": pd.Series(dtype="string"),
        "title": pd.Series(dtype="string"),
        "downloads": pd.Series(dtype="int64"),
        "categories": pd.Series(dtype="object"),
        "game_versions": pd.Series(dtype="object"),
        "highest_game_version": pd.Series(dtype="string"),
    })

    idx = 0

    for _, row in df.iterrows():
        if(row["downloads"] < min_downloads):
            continue

        cats = parse_categories(row["categories"])

        if(len(keep_categories.intersection(cats)) == 0):
            continue

        game_versions = parse_game_versions(row.get("game_versions", []))
        highest_game_version = row.get("highest_game_version", "")
        if(pd.isna(highest_game_version) or highest_game_version == ""):
            highest_game_version = get_highest_game_version(game_versions)

        clean_df.loc[idx] = [
            row["slug"],
            row["project_id"],
            row["title"],
            row["downloads"],
            cats,
            game_versions,
            highest_game_version,
        ]
        idx += 1

    if(group_by_game_version):
        clean_df["_game_version_sort_key"] = clean_df["highest_game_version"].apply(parse_game_version)
        clean_df = clean_df.sort_values(
            by=["_game_version_sort_key", "downloads"],
            ascending=[False, False],
            kind="mergesort",
        )
        clean_df = clean_df.drop(columns=["_game_version_sort_key"])
    else:
        clean_df = clean_df.sort_values(by="downloads", ascending=False, kind="mergesort")

    clean_df = clean_df.head(max_accepted_hits).reset_index(drop=True)

    return clean_df

if(__name__ == "__main__"):
    clean_pack_csv_fs()
