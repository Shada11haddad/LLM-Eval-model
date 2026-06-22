import pandas as pd
from pathlib import Path
import json
from src.generation.clients import judge_client

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from concurrent.futures import ThreadPoolExecutor, as_completed


def detect_task_type(file_path: str):
    """
    Detect task type ONCE when user uploads file.

    Returns:
        open_qa
        rag
    """

    extension = Path(file_path).suffix.lower()

    if extension in [".txt", ".pdf", ".docx"]:
        return "rag"

    elif extension in [".csv", ".xlsx"]:

        if extension == ".csv":
            df = pd.read_csv(file_path, nrows=5)
        else:
            df = pd.read_excel(file_path, nrows=5)

        columns = [c.lower().strip() for c in df.columns]

        has_question = "question" in columns

        has_answer = any(
            col in columns
            for col in ["answer","ground_truth","reference_answer","target_answer"]
        )

        if has_question and has_answer:
            return "open_qa"

        return "open_qa_needs_normalization"

    raise ValueError(f"Unsupported file type: {extension}")

#===== =====
MAX_NORMALIZATION_ROWS = 50
MAX_NORMALIZATION_WORKERS = 20


def _extract_single_row(row_data, q_col, translator):
    """Helper: extract Q&A from a single row (runs in thread pool)"""
    extraction_prompt = f"""
Extract the customer's question and the ideal answer from this data,
translating both to English:

{row_data[q_col]}

Return ONLY valid JSON, no markdown:
{{"question": "...", "reference_answer": "..."}}
"""
    try:
        resp = translator.invoke(extraction_prompt)
        ex_content = resp.content.strip().strip("`").replace("json", "", 1).strip()
        result = json.loads(ex_content)
        return {
            "question": result["question"],
            "reference_answer": result["reference_answer"],
        }
    except Exception as e:
        print(f"    [skip] row failed normalization: {e}")
        return None
    

def normalize_unknown_qa_file(file_path: str) -> pd.DataFrame:
    """
    Handles any CSV/XLSX with unrecognized columns (different language,
    unusual naming, full dialogue instead of clean Q&A) and converts it
    into the standard ['question', 'reference_answer'] format in English.

    Processes up to MAX_NORMALIZATION_ROWS rows (cost/time guard for
    large uploads — e.g. instructor testing with unexpected datasets).
    """
    extension = Path(file_path).suffix.lower()
    df = pd.read_csv(file_path) if extension == ".csv" else pd.read_excel(file_path)

    if len(df) > MAX_NORMALIZATION_ROWS:
        df = df.sample(n=MAX_NORMALIZATION_ROWS, random_state=42).reset_index(drop=True)

    sample_rows = df.head(3).to_dict(orient="records")
    columns_info = list(df.columns)

    detection_prompt = f"""This is tabular data with columns: {columns_info}

Sample rows:
{sample_rows}

Identify which column(s) contain the user's QUESTION (or a dialogue/conversation
that implies a question), and which column(s) contain the ideal/correct ANSWER.

Return ONLY valid JSON, no markdown:
{{"question_column": "...", "answer_column": "...", "needs_extraction": true/false}}

Set needs_extraction to true if the data is a full dialogue (not a clean
question/answer pair) and the same column should be used for both
question_column and answer_column.
"""

    translator  = judge_client
    response = translator.invoke(detection_prompt)
    content = response.content.strip().strip("`").replace("json", "", 1).strip()
    detection = json.loads(content)
    print(f"    [DEBUG] detection result: {detection}")

    q_col = detection["question_column"]
    a_col = detection["answer_column"]
    needs_extraction = detection.get("needs_extraction", False)

   
    if not needs_extraction:
        return pd.DataFrame({
            "question": df[q_col].astype(str),
            "reference_answer": df[a_col].astype(str),
        })

    rows_data = [row for _, row in df.iterrows()]
    results = [None] * len(rows_data)

    with ThreadPoolExecutor(max_workers=MAX_NORMALIZATION_WORKERS) as executor:
        futures = {
            executor.submit(_extract_single_row, row, q_col, translator): i
            for i, row in enumerate(rows_data)
        }
        done = 0
        for future in as_completed(futures):
            i = futures[future]
            results[i] = future.result()
            done += 1
            print(f"    [normalize] {done}/{len(rows_data)} rows done")

    rows = [r for r in results if r is not None]
    return pd.DataFrame(rows)
    
def load_qa_dataset(file_path: str):
    """
    Load QA dataset uploaded by user
    """

    extension = Path(file_path).suffix.lower()

    if extension == ".csv":
        df = pd.read_csv(file_path)

    elif extension == ".xlsx":
        df = pd.read_excel(file_path)

    else:
        raise ValueError("Unsupported QA dataset format")

    return df


def load_document(file_path: str) -> str:
    """
    Load TXT / PDF / DOCX document and return plain text
    """

    extension = Path(file_path).suffix.lower()

    if extension == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    elif extension == ".pdf":
        pages = PyPDFLoader(file_path).load()
        return "\n\n".join(p.page_content for p in pages)

    elif extension == ".docx":
        pages = Docx2txtLoader(file_path).load()
        return "\n\n".join(p.page_content for p in pages)

    raise ValueError(f"Unsupported document format: {extension}")