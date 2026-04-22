from langchain.chat_models import init_chat_model
from orecle_helper import check_modpack_switch
import pandas as pd
from dotenv import load_dotenv
from pack_puller import pull_pack

load_dotenv(override=True)

current_slug = None
current_modpack = None

modpacks_df = pd.read_csv("modpacks.csv")

try:

    print("Speak with the orecle:")
    while True:
        response = input()

        new_slug = check_modpack_switch(response, modpacks_df)
        if(new_slug.lower() != "none"):
            if(current_slug == new_slug):
                print(f"Already in modpack {current_slug}, no switch needed.")
                continue

            current_slug = new_slug
            pull_pack(current_slug)

            print(new_slug)
            
        elif(current_modpack is None):
            print("No modpack selected. Please ask for a modpack to get started.")
            continue
        else:
            print("Responding in current context")

except KeyboardInterrupt:
    print("Exiting...")