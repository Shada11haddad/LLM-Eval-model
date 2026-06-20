import json
import random
import pandas as pd
from tqdm import tqdm

from src.generation.clients import judge_client


def generate_qa_pairs(chunks,questions_per_chunk=1,max_chunks=30):
    """
    Generate synthetic QA dataset from chunks.

    Args:
        chunks: list of document chunks
        questions_per_chunk: how many Q&A pairs to generate per chunk
        max_chunks: max number of chunks to sample from (for cost/time control)

    Returns:
    [
        {
            "question": "...",
            "reference_answer": "...",
            "chunk_index": 0
        }
    ]
    """

    qa_pairs = []

    
    if len(chunks) > max_chunks:
        sampled_chunks = random.sample(chunks, max_chunks)
    else:
        sampled_chunks = chunks

    for chunk in tqdm(sampled_chunks, desc="Generating QA pairs"):

        chunk_text = chunk.page_content

        chunk_id = chunk.metadata.get("chunk_index",-1)

        prompt = f"""
You are creating an evaluation dataset for a Retrieval-Augmented Generation (RAG) system.

Given the context below:

{chunk_text}

Generate {questions_per_chunk} question-answer pairs.

Requirements:
- Questions must be answerable ONLY from the context.
- Answers must be concise and factually correct.
- Avoid trivial questions.
- Prefer informative questions.
- Return ONLY valid JSON.

Format:

[
    {{
        "question": "...",
        "reference_answer": "..."
    }}
]
"""

        try:

            response = judge_client.invoke(prompt)

            result = json.loads(response.content)

            for item in result:

                qa_pairs.append({

                    "chunk_index": chunk_id,

                    "question": item["question"],

                    "reference_answer":
                    item["reference_answer"]

                })

        except Exception as e:

            print(f"Failed on chunk {chunk_id}: {e}")

    return pd.DataFrame(qa_pairs)