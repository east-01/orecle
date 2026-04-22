# Script to clean modpacks
import ast
import pandas as pd

MAX_ACCEPTED_HITS = 100
CSV_IN = "modpacks.csv"
CSV_OUT = "clean_modpacks.csv"
KEEP_CATEGORIES = {"technology", "optimization", "quests"}


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
    keep_categories=KEEP_CATEGORIES,
):
    
    df = pd.read_csv(csv_in)

    clean_df = clean_pack_csv(df, max_accepted_hits, keep_categories)
    clean_df.to_csv(csv_out, index=False)

    return clean_df

def clean_pack_csv(df, max_accepted_hits=MAX_ACCEPTED_HITS, keep_categories=KEEP_CATEGORIES):

    # df["downloads"] = pd.to_numeric(df["downloads"], errors="coerce").fillna(0)
    # df = df.sort_values(by="downloads", ascending=False)

    # Type safe declaration of the dataframe
    clean_df = pd.DataFrame({
        "slug": pd.Series(dtype="string"),
        "project_id": pd.Series(dtype="string"),
        "title": pd.Series(dtype="string"),
        "downloads": pd.Series(dtype="int64"),
        "categories": pd.Series(dtype="object"),
    })

    idx = 0

    for _, row in df.iterrows():
        cats = parse_categories(row["categories"])

        if(len(keep_categories.intersection(cats)) == 0):
            continue

        clean_df.loc[idx] = [
            row["slug"],
            row["project_id"],
            row["title"],
            row["downloads"],
            cats,
        ]
        idx += 1

        if(idx >= max_accepted_hits):
            break

    return clean_df

if(__name__ == "__main__"):
    clean_pack_csv_fs()
