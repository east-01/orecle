# Script to grade Orecle responses across a modpack CSV
import json
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from openai import OpenAI

from orecle_helper import LoadedModpack, switch_modpack
from query_vector_store import query_vector_store
from utils import print_as_orecle, start_spinner

ORECLE_MODEL_NAME = "gpt-5-mini"
GRADER_MODEL_NAME = "gpt-5-mini"
QUERY_SEARCH_MODEL_NAME = "gpt-5-mini"
MODEL_NAME_EMBEDDINGS = "text-embedding-3-large"
CSV_IN = "modpacks_clean.csv"
CSV_OUT = "orecle_grades.csv"
DOWNLOADS_DIR = (Path(__file__).resolve().parent / "modpacks").resolve()
NUM_RESULTS = 8
NUM_GENERATED_QUERIES = 1


def require_openai_api_key():
    load_dotenv(override=True)
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY not set, this is required to run this script. Please add it to your .env for this project.")


def get_modpack_slug(modpack):
    if isinstance(modpack, str):
        return modpack

    return modpack["slug"]


def get_modpack_title(modpack):
    if isinstance(modpack, str):
        return None

    return modpack.get("title")


def get_modpack_specs(modpacks_df, modpacks=None):
    if modpacks is not None:
        return modpacks

    if "slug" not in modpacks_df.columns:
        raise ValueError("Input modpacks CSV must include a 'slug' column.")

    specs = []
    for _, row in modpacks_df.iterrows():
        slug = row.get("slug")
        if pd.isna(slug) or str(slug).strip() == "":
            continue

        spec = {"slug": str(slug)}
        title = row.get("title")
        if not pd.isna(title):
            spec["title"] = str(title)

        specs.append(spec)

    return specs


def load_existing_grades(csv_out):
    csv_out_path = Path(csv_out)
    if not csv_out_path.exists() or csv_out_path.stat().st_size == 0:
        return pd.DataFrame()

    return pd.read_csv(csv_out_path)


def get_resume_specs(modpack_specs, existing_grades_df):
    if existing_grades_df.empty or "slug" not in existing_grades_df.columns:
        return modpack_specs

    saved_slugs = existing_grades_df["slug"].dropna()
    if saved_slugs.empty:
        return modpack_specs

    last_saved_slug = str(saved_slugs.iloc[-1])
    for idx, modpack_spec in enumerate(modpack_specs):
        if get_modpack_slug(modpack_spec) == last_saved_slug:
            print_as_orecle(f"Resuming after last saved slug: {last_saved_slug}")
            return modpack_specs[idx + 1:]

    print_as_orecle(f"Last saved slug {last_saved_slug} was not found in the current modpack list; starting from the beginning.")
    return modpack_specs


def save_grades(csv_out, existing_grades_df, new_rows):
    new_grades_df = pd.DataFrame(new_rows)
    if existing_grades_df.empty:
        grades_df = new_grades_df
    elif new_grades_df.empty:
        grades_df = existing_grades_df
    else:
        grades_df = pd.concat([existing_grades_df, new_grades_df], ignore_index=True)

    grades_df.to_csv(csv_out, index=False)
    return grades_df


def get_explicit_modpack_queries(modpack):
    if isinstance(modpack, str):
        return []

    return modpack.get("queries", [])


def parse_json_response(raw_response):
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass

    json_match = re.search(r"\{.*\}", raw_response, re.DOTALL)
    if json_match is not None:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return {
        "score": None,
        "feedback": raw_response,
    }


def parse_grader_response(raw_response):
    parsed_response = parse_json_response(raw_response)
    if isinstance(parsed_response, dict):
        return parsed_response

    return {
        "score": None,
        "feedback": raw_response,
    }


def source_to_dict(source):
    if isinstance(source, dict):
        return {
            "url": source.get("url"),
            "title": source.get("title"),
        }

    return {
        "url": getattr(source, "url", None),
        "title": getattr(source, "title", None),
    }


def get_web_search_sources(response):
    sources = []

    for output_item in getattr(response, "output", []):
        action = getattr(output_item, "action", None)
        if action is None:
            continue

        for source in getattr(action, "sources", None) or []:
            source_dict = source_to_dict(source)
            if source_dict["url"] is not None:
                sources.append(source_dict)

    return sources


def generate_recipe_queries_for_modpack(
    slug,
    title,
    search_client,
    query_search_model_name=QUERY_SEARCH_MODEL_NAME,
    num_queries=NUM_GENERATED_QUERIES,
):
    model_query = f"""Use web search to find {num_queries} concrete Minecraft recipe question(s) for this Modrinth modpack.

Modpack title: {title}
Modpack slug: {slug}

Prefer recipes documented by the modpack's own pages, wiki, guide, changelog, or community documentation. The question must be answerable by searching the installed recipe corpus later, so avoid broad progression questions and ask for one specific item/block recipe.

Return only JSON with this shape:
{{
  "queries": [
    "In {title}, how do I craft <specific item>?"
  ]
}}
"""

    spinner = start_spinner("Searching web for grader recipe query...")
    try:
        response = search_client.responses.create(
            model=query_search_model_name,
            tools=[{"type": "web_search"}],
            tool_choice="auto",
            include=["web_search_call.action.sources"],
            input=model_query,
        )
    except Exception as exc:
        print_as_orecle(f"Web search query generation failed: {exc}")
        return []
    finally:
        spinner.set()

    parsed_response = parse_json_response(response.output_text)
    queries = parsed_response.get("queries", []) if isinstance(parsed_response, dict) else []
    queries = [query for query in queries if isinstance(query, str) and query.strip()]

    return [
        {
            "query": query,
            "query_source": "web_search",
            "query_search_sources": get_web_search_sources(response),
        }
        for query in queries[:num_queries]
    ]


def get_modpack_query_specs(
    modpack,
    current_modpack,
    search_client,
    query_search_model_name=QUERY_SEARCH_MODEL_NAME,
    num_generated_queries=NUM_GENERATED_QUERIES,
):
    explicit_queries = get_explicit_modpack_queries(modpack)
    if len(explicit_queries) > 0:
        return [
            {
                "query": query,
                "query_source": "manual",
                "query_search_sources": [],
            }
            for query in explicit_queries
        ]

    generated_queries = generate_recipe_queries_for_modpack(
        current_modpack.slug,
        current_modpack.title,
        search_client,
        query_search_model_name=query_search_model_name,
        num_queries=num_generated_queries,
    )

    if len(generated_queries) > 0:
        return generated_queries

    return [
        {
            "query": f"In {current_modpack.title}, what is one useful item recipe and how do I craft it?",
            "query_source": "fallback",
            "query_search_sources": [],
        }
    ]


def grade_orecle_response(query, answer, context, grader_model):
    model_query = f"""Grade this Orecle answer using only the retrieved recipe context as source material.

Return only JSON with these keys:
- score: integer from 0 to 5
- feedback: one concise sentence explaining the score

Rubric:
5 = fully answers the query and is supported by the context
4 = mostly correct, with minor missing detail or uncertainty
3 = partially correct, but incomplete or weakly supported
2 = mostly unsupported or misses the main answer
1 = irrelevant or misleading
0 = no useful answer

Query:
{query}

Orecle answer:
{answer}

Retrieved recipe context:
{context}
"""

    spinner = start_spinner("Waiting for grader LLM...")
    try:
        model_response = grader_model.invoke(model_query)
    finally:
        spinner.set()

    return parse_grader_response(str(model_response.content))


def grade_modpack_query(
    current_modpack: LoadedModpack,
    query_spec,
    orecle_model,
    grader_model,
    num_results=NUM_RESULTS,
    verbose=False,
):
    query = query_spec["query"]
    context = query_vector_store(current_modpack.loaded_vector_store, query, num_results)
    answer = current_modpack.query(query, model=orecle_model, num_results=num_results, verbose=verbose, query_results=context)
    grade = grade_orecle_response(query, answer, context, grader_model)

    return {
        "slug": current_modpack.slug,
        "title": current_modpack.title,
        "query": query,
        "query_source": query_spec.get("query_source"),
        "query_search_sources": json.dumps(query_spec.get("query_search_sources", [])),
        "answer": answer,
        "score": grade.get("score"),
        "feedback": grade.get("feedback"),
        "raw_grade": json.dumps(grade),
    }


def grade_orecle(
    modpacks_df,
    modpacks=None,
    existing_grades_df=None,
    csv_out=None,
    resume=True,
    orecle_model_name=ORECLE_MODEL_NAME,
    grader_model_name=GRADER_MODEL_NAME,
    query_search_model_name=QUERY_SEARCH_MODEL_NAME,
    model_name_embeddings=MODEL_NAME_EMBEDDINGS,
    downloads_dir=DOWNLOADS_DIR,
    num_results=NUM_RESULTS,
    num_generated_queries=NUM_GENERATED_QUERIES,
    verbose=False,
):
    orecle_model = init_chat_model(orecle_model_name)
    grader_model = init_chat_model(grader_model_name)
    search_client = OpenAI()
    rows = []
    existing_grades_df = existing_grades_df if existing_grades_df is not None else pd.DataFrame()
    modpack_specs = get_modpack_specs(modpacks_df, modpacks)
    if resume:
        modpack_specs = get_resume_specs(modpack_specs, existing_grades_df)

    for modpack in modpack_specs:
        slug = get_modpack_slug(modpack)
        print_as_orecle(f"Loading {slug}...")
        try:
            current_modpack = switch_modpack(
                slug,
                modpacks_df=modpacks_df,
                model_name_embedding=model_name_embeddings,
                downloads_dir=downloads_dir,
            )
        except Exception as e:
            print(f"Failed to load {slug}, will skip, error: {e}")
            continue

        query_specs = get_modpack_query_specs(
            modpack,
            current_modpack,
            search_client,
            query_search_model_name=query_search_model_name,
            num_generated_queries=num_generated_queries,
        )

        for query_spec in query_specs:
            query = query_spec["query"]
            print_as_orecle(f"Grading query: {query}")
            grade_row = grade_modpack_query(
                current_modpack,
                query_spec,
                orecle_model,
                grader_model,
                num_results=num_results,
                verbose=verbose,
            )
            rows.append(grade_row)

            if csv_out is not None:
                save_grades(csv_out, existing_grades_df, rows)

    if csv_out is not None:
        return save_grades(csv_out, existing_grades_df, rows)

    if existing_grades_df.empty:
        return pd.DataFrame(rows)

    return pd.concat([existing_grades_df, pd.DataFrame(rows)], ignore_index=True)


def grade_orecle_fs(
    modpacks=None,
    csv_in=CSV_IN,
    csv_out=CSV_OUT,
    resume=True,
    orecle_model_name=ORECLE_MODEL_NAME,
    grader_model_name=GRADER_MODEL_NAME,
    query_search_model_name=QUERY_SEARCH_MODEL_NAME,
    model_name_embeddings=MODEL_NAME_EMBEDDINGS,
    downloads_dir=DOWNLOADS_DIR,
    num_results=NUM_RESULTS,
    num_generated_queries=NUM_GENERATED_QUERIES,
    verbose=False,
):
    require_openai_api_key()

    modpacks_df = pd.read_csv(csv_in)
    existing_grades_df = load_existing_grades(csv_out) if resume else pd.DataFrame()
    grades_df = grade_orecle(
        modpacks_df,
        modpacks=modpacks,
        existing_grades_df=existing_grades_df,
        csv_out=csv_out,
        resume=resume,
        orecle_model_name=orecle_model_name,
        grader_model_name=grader_model_name,
        query_search_model_name=query_search_model_name,
        model_name_embeddings=model_name_embeddings,
        downloads_dir=downloads_dir,
        num_results=num_results,
        num_generated_queries=num_generated_queries,
        verbose=verbose,
    )
    return grades_df


if __name__ == "__main__":
    grade_orecle_fs()
