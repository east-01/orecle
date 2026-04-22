from langchain.chat_models import init_chat_model

def check_modpack_switch(response, modpacks_df, model_name="gpt-5-mini"):
    """ Checks if the user is asking to switch modpacks. If so, returns the name of the modpack to switch to. Otherwise, returns None. """
    model = init_chat_model(model_name)
    modpack_list = list(zip(modpacks_df["title"], modpacks_df["slug"]))
    model_query = f"Check if the user is asking to switch modpacks. If so, respond with only the name of the modpack's slug to switch to using the following list of (title, slug) pairs: {modpack_list}. If the user is not asking to switch, return None. If the target modpack is not in the list, return undefined.\n\nUser response:\n\n{response}"
    model_response = model.invoke(model_query)

    return model_response.content