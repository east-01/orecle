# Script to pull modpacks
import requests
import sys

MAX_ACCEPTED_HITS = 500
PAGE_SIZE = 100

page_num = 0
accepted_hits = 0
viewed_cats=set()

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
        viewed_cats.update(hit["categories"])

    page_num += 1

print(viewed_cats)