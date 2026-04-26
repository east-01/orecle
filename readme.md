
## Orecle

Orecle is an interactive command-line assistant for Minecraft modpack recipe lookup. It can download a Modrinth modpack, extract recipe JSON from the installed mods, build a local Chroma vector store, and answer recipe questions using the retrieved recipe context.

### Setup

Install the Python dependencies and make sure `mrpack-install` is available on your `PATH`.

Create a `.env` file with:

```text
OPENAI_API_KEY=your_api_key_here
```

### Running `orecle.py`

```powershell
python orecle.py [starting_slug] [--verbose]
```

Arguments:

| Argument | Required | Description |
| --- | --- | --- |
| `starting_slug` | No | Modrinth project slug to load immediately when Orecle starts, such as `cobblemon-fabric`. If omitted, Orecle starts without a selected modpack and waits for you to ask to switch to one. |
| `-v`, `--verbose` | No | Prints the raw vector-store retrieval results before each LLM answer. This is useful for debugging whether the right recipe documents were found. |

Examples:

```powershell
python orecle.py
python orecle.py cobblemon-fabric
python orecle.py cobblemon-fabric --verbose
```

### What `orecle.py` does

1. Loads environment variables from `.env` and requires `OPENAI_API_KEY`.
2. Loads `modpacks.csv`, which maps modpack titles to Modrinth slugs.
3. Initializes the chat model used to classify modpack-switch requests and answer questions.
4. If `starting_slug` is provided, calls `switch_modpack()` to prepare that modpack.
5. Enters an interactive prompt loop.
6. For each user message, asks the model whether the user wants to switch modpacks.
7. When switching modpacks, it downloads the pack if needed, extracts recipes, loads recipe documents, and builds or opens the pack-specific vector store.
8. When a modpack is selected and the message is a recipe question, it retrieves relevant recipe documents and sends them to the model as context.

The main helper path is:

```text
orecle.py
  -> switch_modpack()
  -> pull_pack()
  -> extract_recipes()
  -> load_json_docs()
  -> build_vector_store()
  -> LoadedModpack.query()
  -> query_vector_store()
```

## Modrinth API

Modrinth is a mod/modpack repository that we'll use, it has an api so we can easily download modpacks locally.
There are three steps to downloading the modpacks from modrinth: getting list of modpack info, cleaning list of info, and then downloading actual modpack files from cleaned list.

**1.** Run `download_pack_csv.py` to get a csv of all the modpacks in Modrinth.

**2.** Using `category_viewer.py` we can see that the category list is:
```
{'technology', 'optimization', 'utility', 'quests', 'combat', 'food', 'economy', 'iris', 'mobs', 'modloader', 'neoforge', 'worldgen', 'fabric', 'decoration', 'storage', 'kitchen-sink', 'challenging', 'minigame', 'cursed', 'magic', 'transportation', 'library', 'game-mechanics', 'adventure', 'lightweight', 'management', 'equipment', 'quilt', 'minecraft', 'social', 'forge', 'datapack', 'multiplayer'}
```

Since we want to get modpacks with complex recipes, we'll look for modpacks with `technology` or `optimization` categories.

Run `clean_pack_csv.py` to clean the csv and get a list of modpacks that actually want to download and use in our dataset.

**3.** Run `pack-puller.py` to download all of the modpacks in the specified CSV to a directory.

### mrpack-install

[mrpack-install](https://github.com/nothub/mrpack-install) is a command line tool for installing modpacks. It can take a modrinth slug and do all of the heavy lifting, used in `download_pack_csv.py`.

### Specific API endpoint examples

get list of version ids:
```https://api.modrinth.com/v2/project/cobblemon-fabric```
look at a specific version:
```https://api.modrinth.com/v2/project/cobblemon-fabric/version/Lydu1ZNoa```
