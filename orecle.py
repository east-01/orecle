import argparse
import os
from langchain.chat_models import init_chat_model
from orecle_helper import *
from utils import *
import pandas as pd
from dotenv import load_dotenv

MODEL_NAME="gpt-5-mini"
MODEL_NAME_EMBEDDINGS="text-embedding-3-large"
DOWNLOADS_DIR = (Path(__file__).resolve().parent / "modpacks").resolve()

parser = argparse.ArgumentParser()
parser.add_argument("starting_slug", nargs="?", help="Optional modpack slug to load on startup.")
parser.add_argument("-v", "--verbose", action="store_true", help="Print retrieved vector store data before each LLM response.")
args = parser.parse_args()

load_dotenv(override=True)
if not os.environ.get("OPENAI_API_KEY"):
    print("OPENAI_API_KEY not set, this is required to run this script. Please add it to your .env for this project.")
    exit(1)

modpacks_df = pd.read_csv("modpacks.csv")

current_modpack: LoadedModpack = None
model = init_chat_model(MODEL_NAME)

try:

    if args.starting_slug:
        current_modpack = switch_modpack(args.starting_slug, modpacks_df=modpacks_df, downloads_dir=DOWNLOADS_DIR)
        print_as_orecle(f"Switched to {current_modpack.title}, ask the orecle anything:")
    else:
        print_as_orecle("Speak with the orecle:")
    
    while True:
        response = input_to_orecle()

        new_slug = check_modpack_switch(response, modpacks_df, model_name=MODEL_NAME)
        if(new_slug.lower() != "none"):

            if(current_modpack is not None and current_modpack.slug == new_slug):
                print_as_orecle(f"Already in modpack {current_modpack.title}, no switch needed.")
                continue

            current_modpack = switch_modpack(new_slug, modpacks_df=modpacks_df, downloads_dir=DOWNLOADS_DIR)
            print_as_orecle(f"Switched to {current_modpack.title}, ask the orecle anything:")
            continue

        elif(current_modpack is None):

            print_as_orecle("No modpack selected. Please ask for a modpack to get started.")
            continue

        print_as_orecle(current_modpack.query(response, model=model, num_results=8, verbose=args.verbose))

except KeyboardInterrupt:
    print("Exiting...")
