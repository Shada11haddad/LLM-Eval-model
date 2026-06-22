"""
ragas_eval.py — RAGAS scoring for the RAG track ONLY.

Runs ALONGSIDE the GPT-judge (does not replace it). Adds the official RAGAS
metrics — faithfulness, answer relevancy, context precision, context recall —
as extra columns on the RAG results.

Written for the ragas 0.4.x API (SingleTurnSample / EvaluationDataset / metric
classes).

Two robustness features:
  1. An import shim (top of file) works around a ragas 0.4.x upstream bug
     (GitHub ragas #2741): ragas hard-imports
     `langchain_community.chat_models.vertexai`, a module removed from modern
     langchain-community. We never use VertexAI, so we stub it so ragas imports.
  2. Fails safe: if ragas is missing or errors out, it returns empty scores so
     the main evaluation still completes. It will never crash your run.
"""

# ---------------------------------------------------------------------------
# Import shim — MUST run before ragas is imported (ragas #2741).
# Registers harmless stubs for any missing `langchain_community.chat_models.*`
# module so ragas 0.4.x imports cleanly against modern langchain-community.
# ---------------------------------------------------------------------------
import sys
import types
import importlib.util
import importlib.abc
import importlib.machinery


class _StubLoader(importlib.abc.Loader):
    def create_module(self, spec):
        module = types.ModuleType(spec.name)

        def _getattr(attr):
            def _blocked(*args, **kwargs):
                raise ImportError(f"{spec.name}.{attr} is a stub (provider not installed).")
            return type(attr, (), {"__init__": _blocked})

        module.__getattr__ = _getattr
        return module

    def exec_module(self, module):
        pass


class _StubFinder(importlib.abc.MetaPathFinder):
    _PREFIX = "langchain_community.chat_models."

    def find_spec(self, fullname, path=None, target=None):
        if not fullname.startswith(self._PREFIX):
            return None
        sys.meta_path.remove(self)
        try:
            real = importlib.util.find_spec(fullname)
        except Exception:
            real = None
        finally:
            sys.meta_path.insert(0, self)
        if real is not None:
            return None
        return importlib.machinery.ModuleSpec(fullname, _StubLoader())


if not any(isinstance(f, _StubFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _StubFinder())
# ---------------------------------------------------------------------------

import pandas as pd
from config import cfg


def ragas_score_batch(samples: list) -> pd.DataFrame:
    """
    Score a batch of RAG samples with RAGAS (ragas 0.4.x API).

    Args:
        samples: list of dicts, each with:
            - "question"  (str)
            - "answer"    (str)         the model's answer
            - "contexts"  (list[str])   retrieved context chunks
            - "reference" (str)         the ground-truth answer

    Returns:
        DataFrame, one row per sample, columns:
            ragas_faithfulness, ragas_answer_relevancy,
            ragas_context_precision, ragas_context_recall
        (None-filled if ragas is unavailable or fails.)
    """
    n = len(samples)
    empty = pd.DataFrame({
        "ragas_faithfulness": [None] * n,
        "ragas_answer_relevancy": [None] * n,
        "ragas_context_precision": [None] * n,
        "ragas_context_recall": [None] * n,
    })

    if n == 0:
        return empty

    # Import inside the function so a missing/broken ragas install doesn't
    # crash the whole app at import time — it just skips RAGAS.
    try:
        from ragas import evaluate
        from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
        from ragas.metrics import (
            Faithfulness,
            ResponseRelevancy,
            LLMContextPrecisionWithReference,
            LLMContextRecall,
        )
        from ragas.llms import LangchainLLMWrapper
        from ragas.embeddings import LangchainEmbeddingsWrapper
        from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    except Exception as e:
        print(f"[ragas] library not available — skipping RAGAS scores: {e}")
        return empty

    try:
        # Evaluator LLM + embeddings passed EXPLICITLY so ragas never tries to
        # auto-pick a provider.
        evaluator_llm = LangchainLLMWrapper(
            ChatOpenAI(model="gpt-4o", temperature=0, api_key=cfg.OPENAI_API_KEY)
        )
        evaluator_emb = LangchainEmbeddingsWrapper(
            OpenAIEmbeddings(model=cfg.EMBEDDING_MODEL, api_key=cfg.OPENAI_API_KEY)
        )

        # ragas 0.4.x: build typed samples, then an EvaluationDataset.
        eval_samples = [
            SingleTurnSample(
                user_input=s["question"],
                response=s["answer"],
                retrieved_contexts=list(s["contexts"]) if s.get("contexts") else [],
                reference=s["reference"],
            )
            for s in samples
        ]
        dataset = EvaluationDataset(samples=eval_samples)

        # ragas 0.4.x: metrics are CLASSES, each initialized with the LLM
        # (answer relevancy also needs embeddings).
        faith = Faithfulness(llm=evaluator_llm)
        relev = ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_emb)
        cprec = LLMContextPrecisionWithReference(llm=evaluator_llm)
        crec = LLMContextRecall(llm=evaluator_llm)

        result = evaluate(dataset=dataset, metrics=[faith, relev, cprec, crec])
        rdf = result.to_pandas().reset_index(drop=True)

        # Pull each column by the metric's own name (robust to naming changes).
        return pd.DataFrame({
            "ragas_faithfulness":      rdf.get(faith.name),
            "ragas_answer_relevancy":  rdf.get(relev.name),
            "ragas_context_precision": rdf.get(cprec.name),
            "ragas_context_recall":    rdf.get(crec.name),
        })

    except Exception as e:
        print(f"[ragas] scoring failed — returning empty scores: {e}")
        return empty