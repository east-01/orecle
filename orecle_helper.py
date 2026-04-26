from langchain.chat_models import init_chat_model
from dataclasses import dataclass
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from pathlib import Path

from utils import *
from pack_puller import pull_pack
from build_vector_store import build_vector_store, load_json_docs
from query_vector_store import query_vector_store
from extract_recipes import extract_recipes

#region Loaded modpack
@dataclass(frozen=True)
class LoadedModpack():
    """ A representation of a loaded modpack in memory- contains model info and vector store """
    slug: str
    title: str
    embeddings: OpenAIEmbeddings
    loaded_vector_store: Chroma

    def query(self, query, model, num_results=1, verbose=False):
        query_results = query_vector_store(self.loaded_vector_store, query, num_results)

        if verbose:
            print_as_orecle("Retrieved vector store data:")
            print(query_results)

        model = init_chat_model("gpt-5-mini")
        model_query = f"Use the following context to answer this query:\n\nQuery:\n\n{query}\n\nContext:\n\n{query_results}"
        spinner = start_spinner("Waiting for LLM...")
        try:
            model_response = model.invoke(model_query)
        finally:
            spinner.set()
        
        return model_response.content


def check_modpack_switch(response, modpacks_df, model_name="gpt-5-mini"):
    """ Checks if the user is asking to switch modpacks. If so, returns the name of the modpack to switch to. Otherwise, returns None. """
    model = init_chat_model(model_name)
    modpack_list = list(zip(modpacks_df["title"], modpacks_df["slug"]))
    model_query = f"Check if the user is asking to use a modpack or switch modpacks. If so, respond with only the name of the modpack's slug to switch to using the following list of (title, slug) pairs: {modpack_list}. If the user is not asking to switch, return None. If the target modpack is not in the list, return undefined.\n\nUser response:\n\n{response}"
    spinner = start_spinner("Waiting for LLM...")
    try:
        model_response = model.invoke(model_query)
    finally:
        spinner.set()

    return model_response.content


def switch_modpack(slug, modpacks_df, model_name_embedding="text-embedding-3-large", downloads_dir="modpacks") -> LoadedModpack:

    modpack_match = modpacks_df.loc[modpacks_df["slug"] == slug, "title"]
    if(modpack_match.empty):
        raise Exception(f"Failed to switch to modpack slug \"{slug}\" it does not resolve in the modpacks CSV.")

    modpack_directory = pull_pack(slug, downloads_dir=downloads_dir)

    extract_recipes(modpack_directory)

    recipes_path = modpack_directory / "recipes"

    print_as_orecle(f"Loading data...")

    json_docs = load_json_docs(recipes_path)
    if(json_docs is None):
        raise RuntimeError(f"No recipe documents found under {recipes_path}")

    embeddings, vector_store = build_vector_store(
        recipes_directory=str(modpack_directory),
        vector_store_directory=str(modpack_directory / "vectorstore"),
        embedding_model=model_name_embedding,
        collection_name="recipes"
    )

    vector_store.add_documents(documents=json_docs)

    return LoadedModpack(
        slug=slug,
        title=modpack_match.iloc[0],
        embeddings=embeddings,
        loaded_vector_store=vector_store
    )
#endregion
