import os
from dotenv import load_dotenv
from pathlib import Path
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Initialize constants, could make these passable via args...
VECTOR_STORE_DIRECTORY = "orecle_vector_store"
EMBEDDING_MODEL = "text-embedding-3-large"
RECIPES_DIRECTORY = "recipes"
COLLECTION_NAME = "recipes"
CHUNK_SIZE_MAX = 1000
CHUNK_SIZE_MIN = 100

def load_json_docs(json_docs_path: Path) -> list[Document]:
    """
    Load JSON documents from given path as a list of langchain Document.
    """
    json_docs_list = sorted(json_docs_path.glob("*.json"))
    json_docs: list[Document] = []

    # Break up each gian JSON file into individual objects, stored as list of langchain Document
    for json_doc in json_docs_list:
        loader = JSONLoader(
            file_path=json_doc,
            jq_schema=".[] | {source_mod, source_modpack, source_path, raw}",
            text_content=False,
        )
        
        docs = loader.load()
        json_docs.extend(docs)

    return json_docs

def build_vector_store(
    recipes_directory=RECIPES_DIRECTORY,
    vector_store_directory=VECTOR_STORE_DIRECTORY,
    embedding_model=EMBEDDING_MODEL,
    collection_name=COLLECTION_NAME,
) -> None:
    """Create a vector store using JSON recipes from the given directory."""
    load_dotenv()

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set, this is required to run this script. Please add it to your .env for this project.")
        return None

    recipes_path = Path(recipes_directory)

    if not recipes_path.exists():
        print(f"Recipes directory not found at: {recipes_path}. Please generate the recipes directory first.")
        return None
    
    # Initialize models
    embeddings = OpenAIEmbeddings(model=embedding_model)
    vector_store_path = Path(vector_store_directory)
    
    # Make the vectore store path if it does not yet exist
    if not vector_store_path.exists():
        os.makedirs(vector_store_path, exist_ok=True)
    
    # Create a collection in the given vector store, may contain more than one collection
    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=vector_store_directory
    )

    vector_store_is_empty = vector_store._collection.count() == 0

    # Only build the vector store if it is empty
    if vector_store_is_empty:
        json_docs = load_json_docs(recipes_path)
        vector_store.add_documents(documents=json_docs)

    return vector_store

if __name__ == "__main__":
    build_vector_store()
