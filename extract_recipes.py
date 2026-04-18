import os
import json
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

def normalize_recipe(recipe: Dict[str, Any], source_mod: str, source_modpack: str, source_path: str) -> Dict[str, Any]:
    """
    Convert a raw Minecraft/mod recipe JSON into a simpler normalized form.
    """
    recipe_type = recipe.get("type", "unknown")
    result = extract_result(recipe)

    normalized: Dict[str, Any] = {
        "source_mod": source_mod,
        "source_modpack": source_modpack,
        "source_path": source_path,
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
            # Typical modern recipe path
            if name.startswith("data/") and "/recipes/" in name and name.endswith(".json"):
                recipe_files.append(name)

    return recipe_files

def extract_recipes_from_jar(jar_path: Path) -> List[Dict[str, Any]]:
    """
    Read and normalize all recipes from one jar.
    """
    recipes: List[Dict[str, Any]] = []
    source_mod = jar_path.stem
    source_modpack = jar_path.parts[1]

    try:
        with zipfile.ZipFile(jar_path, "r") as jar:
            for recipe_file in find_recipe_files_in_jar(jar_path):
                try:
                    with jar.open(recipe_file) as f:
                        raw = json.load(f)
                    normalized = normalize_recipe(raw, source_mod, source_modpack, recipe_file)
                    recipes.append(normalized)
                except Exception as e:
                    recipes.append({
                        "source_mod": source_mod,
                        "source_modpack": source_modpack,
                        "source_path": recipe_file,
                        "error": str(e),
                    })
    except zipfile.BadZipFile:
        print(f"Skipping invalid jar: {jar_path}")

    return recipes

def scan_mods_directory(mods_directory: str) -> List[Dict[str, Any]]:
    """
    Scan every .jar in the mods directory and extract recipe data.
    """
    mods_path = Path(mods_directory)
    all_recipes: List[Dict[str, Any]] = []

    if not mods_path.exists():
        print(f"Mods directory not found: {mods_directory}")

    jar_files = sorted(mods_path.glob("*.jar"))
    print(f"Scanning {mods_path}.\nFound {len(jar_files)} jar files.")

    for jar_path in jar_files:
        jar_recipes = extract_recipes_from_jar(jar_path)
        all_recipes.extend(jar_recipes)

    return all_recipes

def scan_modpacks_directory(modpacks_directory: str) -> List[str]:
    """
    Scan the modpacks directory to find the paths for all the mods.
    """

    modpacks_path = Path(modpacks_directory)
    mods_directories: List[str] = []

    if not modpacks_path.exists():
        print(f"Error: Modpacks directory not found: {modpacks_directory}")
        return mods_directories

    modpacks = sorted(modpacks_path.iterdir())
    print(f"Found {len(modpacks)} modpacks")
    
    for modpack in modpacks:
        modpack_mods_directory = Path(modpack) / "mc" / "mods"
        
        if not modpack_mods_directory.exists():
            print(f"Error: modpack {modpack} mods directory not found.")
            continue
            
        mods_directories.append(str(modpack_mods_directory))

    return mods_directories

def main():
    modpacks_directory = "modpacks"
    recipes_directory = Path("recipes")

    if not recipes_directory.exists():
        os.makedirs(recipes_directory, exist_ok=True)

    mods_directories = scan_modpacks_directory(modpacks_directory)

    for mods_directory in mods_directories:
        modpack_name = mods_directory.split("/")[1]
        output_filename = f"{modpack_name}-recipes.json"
        output_file = recipes_directory / output_filename

        recipes = scan_mods_directory(mods_directory)
    
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(recipes, f, indent=2, ensure_ascii=False)
    
        print(f"Saved {len(recipes)} recipes to {output_file}")


if __name__ == "__main__":
    main()
