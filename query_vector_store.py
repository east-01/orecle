# Imports
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from pathlib import Path

# Initialize constants, could make these passable via args...
VECTOR_STORE_DIRECTORY = "orecle_vector_store"
EMBEDDING_MODEL = "text-embedding-3-large"
COLLECTION_NAME = "recipes"
NUM_RESULTS = 3

def run_query(vector_store: Chroma, query: str, num_results: int) -> str:
    """ Runs user query agasint vector store using similarity with score """
    retrieved_docs = vector_store.similarity_search_with_score(query, k=num_results)

    retrieved_docs_serialized = "\n\n".join(
            (f"Source: {doc.metadata}\nScore: {score}\nContent: {doc.page_content}")
        for doc, score in retrieved_docs
    )

    return retrieved_docs_serialized

def main():
    load_dotenv()

    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY not set, this is required to run this script. Please add it to your .env for this project.")
        return None
    
    vector_store_path = Path(VECTOR_STORE_DIRECTORY)

    # Make the vectore store path if it does not yet exist
    if not vector_store_path.exists():
        print(f"Error: Vector store not found at path {vector_store_path}. Please create the vector store before trying to query it.")
        return None
    
    # Initialize models
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    # Create a collection in the given vector store, may contain more than one collection
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=VECTOR_STORE_DIRECTORY
    )

    vector_store_is_empty = vector_store._collection.count() == 0

    if not vector_store_is_empty:
        query = "In the cobblemon modpack, how do I get the apricorn bench recipe?"
        num_results = NUM_RESULTS 
        
        query_results = run_query(vector_store, query, num_results)
        #print(query_results)

        model = init_chat_model("gpt-5-mini")
        model_query = f"Use the following context to answer this query:\n\nQuery:\n\n{query}\n\nContext:\n\n{query_results}"
        model_response = model.invoke(model_query)
        print(model_response.content)



if __name__ == "__main__":
    main()


