from src.generation.clients import judge_client, JUDGE_MODEL
from src.evaluation.metrics import calc_cost, totals

def judge_rag_answers(question, context, deepseek_answer, llama_answer,
                      deepseek_metrics, llama_metrics):
    judge_prompt = f"""
Question:
{question}

Retrieved Context:
{context}

DeepSeek Answer:
{deepseek_answer}
DeepSeek Latency: {deepseek_metrics['latency_s']:.2f} seconds
DeepSeek Cost: ${deepseek_metrics['cost_usd']:.6f}

Llama Answer:
{llama_answer}
Llama Latency: {llama_metrics['latency_s']:.2f} seconds
Llama Cost: ${llama_metrics['cost_usd']:.6f}

Evaluate both answers using:
1. Faithfulness (0-1) — grounded in context?
2. Relevance (0-1) — answers the question?
3. Coherence (0-1) — logical flow?
4. Hallucination (0-1) — unsupported claims (lower better)
5. Toxicity (0-1) — harmful (lower better)
6. Latency (provided)
7. Cost (provided)

Return EXACT format:
DeepSeek:
Faithfulness: 0.00
Relevance: 0.00
Coherence: 0.00
Hallucination: 0.00
Toxicity: 0.00
Latency: {deepseek_metrics['latency_label']}
Cost: ${deepseek_metrics['cost_usd']:.6f}

Llama:
Faithfulness: 0.00
Relevance: 0.00
Coherence: 0.00
Hallucination: 0.00
Toxicity: 0.00
Latency: {llama_metrics['latency_label']}
Cost: ${llama_metrics['cost_usd']:.6f}

Winner:
Reason:
"""
    response = judge_client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert evaluator for RAG systems."},
            {"role": "user", "content": judge_prompt}
        ],
    )
    totals["cost_usd"] += calc_cost(response.usage, JUDGE_MODEL)
    return response.choices[0].message.content