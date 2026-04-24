from langchain.chat_models import init_chat_model
from dataclasses import dataclass
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from pathlib import Path

from utils import start_spinner
from pack_puller import pull_pack
from build_vector_store import build_vector_store

#region I/O Utils
def print_as_orecle(message):
    print(f"Orecle > {message}")


def input_to_orecle():
    print("You > ", end="")
    return input()
#endregion

#region Loaded modpack
@dataclass(frozen=True)
class LoadedModpack():
    """ A representation of a loaded modpack in memory- contains model info and vector store """
    slug: str
    title: str
    loaded_vector_store: Chroma

def check_modpack_switch(response, modpacks_df, model_name="gpt-5-mini"):
    """ Checks if the user is asking to switch modpacks. If so, returns the name of the modpack to switch to. Otherwise, returns None. """
    model = init_chat_model(model_name)
    modpack_list = list(zip(modpacks_df["title"], modpacks_df["slug"]))
    model_query = f"Check if the user is asking to switch modpacks. If so, respond with only the name of the modpack's slug to switch to using the following list of (title, slug) pairs: {modpack_list}. If the user is not asking to switch, return None. If the target modpack is not in the list, return undefined.\n\nUser response:\n\n{response}"
    spinner = start_spinner("Waiting for LLM...")
    try:
        model_response = model.invoke(model_query)
    finally:
        spinner.set()

    return model_response.content

def run_query(vector_store: Chroma, query: str, num_results: int) -> str:
    """ Runs user query agasint vector store using similarity with score """

    spinner = start_spinner("Waiting for LLM...")
    try:
        retrieved_docs = vector_store.similarity_search_with_score(query, k=num_results)
    finally:
        spinner.set()

    retrieved_docs_serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nScore: {score}\nContent: {doc.page_content}")
        for doc, score in retrieved_docs
    )

    return retrieved_docs_serialized

def switch_modpack(slug, modpacks_df, model_name="gpt-5-mini", model_name_embedding="text-embedding-3-large", downloads_dir="modpacks") -> LoadedModpack:

    modpack_match = modpacks_df.loc[modpacks_df["slug"] == slug, "title"]
    if(modpack_match.empty):
        raise Exception(f"Failed to switch to modpack slug \"{slug}\" it does not resolve in the modpacks CSV.")

    pull_pack(slug, downloads_dir=downloads_dir)
    mods_directory = Path(downloads_dir) / slug / "mc" / "mods"
    if(not mods_directory.exists()):
        raise Exception(f"Failed to find pulled mods directory at \"{str(mods_directory)}\"")

    vector_store = build_vector_store()

    return LoadedModpack(
        slug=slug,
        title=modpack_match.iloc[0],
        loaded_vector_store=vector_store
    )
    pass


#endregion