
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