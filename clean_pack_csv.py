# Script to clean modpacks
import ast
import pandas as pd

MAX_ACCEPTED_HITS = 100
CSV_IN = "modpacks.csv"
CSV_OUT = "clean_modpacks.csv"
KEEP_CATEGORIES = {"technology", "optimization"}


def parse_categories(cats):
    if(pd.isna(cats)):
        return []

    if(isinstance(cats, list)):
        return cats

    try:
        parsed_cats = ast.literal_eval(cats)
        if(isinstance(parsed_cats, list)):
            return parsed_cats
    except (ValueError, SyntaxError):
        pass

    return []


# Type safe declaration of the dataframe
clean_df = pd.DataFrame({
    "slug": pd.Series(dtype="string"),
    "project_id": pd.Series(dtype="string"),
    "title": pd.Series(dtype="string"),
    "downloads": pd.Series(dtype="int64"),
    "categories": pd.Series(dtype="object"),
})

df = pd.read_csv(CSV_IN)
# df["downloads"] = pd.to_numeric(df["downloads"], errors="coerce").fillna(0)
# df = df.sort_values(by="downloads", ascending=False)

idx = 0

for _, row in df.iterrows():
    cats = parse_categories(row["categories"])

    if(len(KEEP_CATEGORIES.intersection(cats)) == 0):
        continue

    clean_df.loc[idx] = [
        row["slug"],
        row["project_id"],
        row["title"],
        row["downloads"],
        cats,
    ]
    idx += 1

    if(idx >= MAX_ACCEPTED_HITS):
        break

clean_df.to_csv(CSV_OUT, index=False)
