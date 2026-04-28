import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

def normalize_ingredient(ingredient: Any) -> Any:
    """
    Normalize a recipe ingredient into a simpler representation.

    Handles:
    - {"item": "..."}
    - {"tag": "..."}
    - [{"item": "..."}, {"item": "..."}]  # alternatives
    """
    if isinstance(ingredient, list):
        return [normalize_ingredient(x) for x in ingredient]

    if isinstance(ingredient, dict):
        if "item" in ingredient:
            return {"type": "item", "value": ingredient["item"]}
        if "tag" in ingredient:
            return {"type": "tag", "value": ingredient["tag"]}

        # fallback for mod-specific ingredient structures
        return {"type": "unknown", "value": ingredient}

    return ingredient

def extract_result(recipe: Dict[str, Any]) -> Optional[Any]:
    """
    Extract the output/result field from common recipe formats.
    """
    if "result" not in recipe:
        return None

    result = recipe["result"]

    if isinstance(result, str):
        return {"item": result, "count": 1}

    if isinstance(result, dict):
        item = result.get("item")
        count = result.get("count", 1)
        tag = result.get("tag")
        if item:
            return {"item": item, "count": count}
        if tag:
            return {"tag": tag, "count": count}
        return result

    return result

def normalize_recipe(recipe: Dict[str, Any], source_mod: str, source_modpack: str, source_path: str, source_file: str) -> Dict[str, Any]:
    """
    Convert a raw Minecraft/mod recipe JSON into a simpler normalized form.
    """
    recipe_type = recipe.get("type", "unknown")
    result = extract_result(recipe)

    normalized: Dict[str, Any] = {
        "source_mod": source_mod,
        "source_modpack": source_modpack,
        "source_path": source_path,
        "source_file": source_file,
        "type": recipe_type,
        "result": result,
        "inputs": [],
        "raw": recipe,  # keep original for debugging / future parsing
    }

    # Standard shaped crafting
    if "pattern" in recipe and "key" in recipe:
        key = recipe.get("key", {})
        normalized["inputs"] = {
            symbol: normalize_ingredient(value)
            for symbol, value in key.items()
        }
        normalized["pattern"] = recipe.get("pattern", [])

    # Standard shapeless crafting
    elif "ingredients" in recipe:
        normalized["inputs"] = [normalize_ingredient(x) for x in recipe["ingredients"]]

    # Single ingredient machine recipes or smelting-like recipes
    elif "ingredient" in recipe:
        normalized["inputs"] = [normalize_ingredient(recipe["ingredient"])]

    return normalized

def find_recipe_files_in_jar(jar_path: Path) -> List[str]:
    """
    Return all recipe JSON paths inside a jar.
    """
    recipe_files = []

    with zipfile.ZipFile(jar_path, "r") as jar:
        for name in jar.namelist():
            # Support both legacy and modern datapack recipe paths while skipping advancement unlocks.
            if (
                name.startswith("data/")
                and name.endswith(".json")
                and (
                    "/recipes/" in name 
                    or "/recipe/" in name
                    or "/tags/" in name
                )
                and "/advancement/" not in name
                and "/advancements/" not in name
            ):
                recipe_files.append(name)

    return recipe_files

def extract_recipes_from_jar(jar_path: Path, source_modpack: str) -> List[Dict[str, Any]]:
    """
    Read and normalize all recipes from one jar.
    """
    recipes: List[Dict[str, Any]] = []
    source_mod = jar_path.stem

    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            for recipe_file in find_recipe_files_in_jar(jar_path):
                source_file = Path(recipe_file).stem 
                try:
                    with jar.open(recipe_file) as f:
                        raw = json.load(f)
                    normalized = normalize_recipe(raw, source_mod, source_modpack, recipe_file, source_file)
                    recipes.append(normalized)
                except Exception as e:
                    recipes.append({
                        "source_mod": source_mod,
                        "source_modpack": source_modpack,
                        "source_path": recipe_file,
                        "source_file": source_file,
                        "error": str(e),
                    })
    except zipfile.BadZipFile:
        print(f"Skipping invalid jar: {jar_path}")

    return recipes

def scan_mods_directory(mods_directory: Path) -> List[Path]:
    """
    Return all .jar files in a modpack's mods directory.
    """
    if not mods_directory.exists():
        print(f"Mods directory not found: {mods_directory}")
        return []

    jar_files = sorted(mods_directory.glob("*.jar"))
    # print(f"Scanning {mods_directory}.")
    # print(f"Found {len(jar_files)} jar files.")
    return jar_files


def extract_recipes(modpack_directory: str, recipes_directory: str = "recipes") -> List[Path]:
    """
    Extract recipes for a single modpack directory and write one JSON file per jar.
    """
    modpack_path = Path(modpack_directory)
    modpack_name = modpack_path.name
    mods_directory = modpack_path / "mc" / "mods"
    output_directory = modpack_path / recipes_directory

    if not modpack_path.exists():
        print(f"Modpack directory not found: {modpack_directory}")
        return []

    if not mods_directory.exists():
        print(f"Mods directory not found: {mods_directory}")
        return []

    output_directory.mkdir(parents=True, exist_ok=True)
    output_files: List[Path] = []

    for jar_path in scan_mods_directory(mods_directory):
        recipes = extract_recipes_from_jar(jar_path, modpack_name)
        if(len(recipes) == 0):
            continue

        output_file = output_directory / f"{jar_path.stem}-recipes.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False)

        # print(f"Saved {len(recipes)} recipes to {output_file}")
        output_files.append(output_file)

    return output_files


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_recipes.py <modpack_directory>")
    else:
        extract_recipes(sys.argv[1])
