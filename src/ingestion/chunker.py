from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
from config import cfg
from loguru import logger


def chunk_documents(docs: List[Document], chunk_size: int = None, chunk_overlap: int = None) -> List[Document]:
    chunk_size = chunk_size if chunk_size is not None else cfg.CHUNK_SIZE
    chunk_overlap = chunk_overlap if chunk_overlap is not None else cfg.CHUNK_OVERLAP
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(docs)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
    logger.info(f"Split {len(docs)} documents into {len(chunks)} chunks "
                f"(size={chunk_size}, overlap={chunk_overlap})")
    return chunks