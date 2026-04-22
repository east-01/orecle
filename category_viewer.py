# Script to pull modpacks
import requests
import sys

PAGE_SIZE = 500

def view_categories(page_size=PAGE_SIZE):
    page_num = 0
    viewed_cats=set()

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
            viewed_cats.update(hit["categories"])

        page_num += 1

    return viewed_cats


if(__name__ == "__main__"):
    print(view_categories())
