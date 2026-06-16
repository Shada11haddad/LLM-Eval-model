import pandas as pd
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader


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
            for col in [
                "answer",
                "ground_truth",
                "reference_answer"
            ]
        )

        if has_question and has_answer:
            return "open_qa"

        raise ValueError("Dataset must contain question and answer columns")

    raise ValueError(f"Unsupported file type: {extension}")


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