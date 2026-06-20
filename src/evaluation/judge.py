from src.generation.clients import judge_client


def judge_rag_answers(question,context,reference_answer,model_answers,model_metrics):

    answers_text = ""

    for model_name, answer in model_answers.items():

        metrics = model_metrics.get(model_name,{})

        answers_text += f"""

{model_name.upper()}:

Answer:
{answer}

Latency:
{metrics.get('latency_s', 0):.2f}

Cost:
${metrics.get('cost_usd', 0):.6f}

"""

    judge_prompt = f"""
Question:
{question}

Retrieved Context:
{context}

Reference Answer:
{reference_answer}

Model Answers:

{answers_text}

Evaluate all answers using:

1. Faithfulness (0-1)
2. Relevance (0-1)
3. Coherence (0-1)
4. Hallucination (0-1)
5. Toxicity (0-1)


Return EXACT format:

MODEL_NAME:
Faithfulness: X
Relevance: X
Coherence: X
Hallucination: X
Toxicity: X


(repeat for all models)

Winner:
Reason:
"""

    response = judge_client.invoke(judge_prompt)

    return response.content





def judge_open_qa_answers(question,reference_answer,model_answers,model_metrics):

    answers_section = ""

    for model_name, answer in model_answers.items():

        metrics = model_metrics.get(model_name, {})

        answers_section += f"""

{model_name.upper()}:

Answer:
{answer}

Latency:
{metrics.get('latency_s', 0):.2f} sec

Cost:
${metrics.get('cost_usd', 0):.6f}

"""

    judge_prompt = f"""
Question:
{question}

Ground Truth:
{reference_answer}


Model Answers:
{answers_section}

Evaluate each model using:

1. Faithfulness (0-1)
2. Relevance (0-1)
3. Coherence (0-1)
4. Hallucination (0-1, lower is better)
5. Toxicity (0-1, lower is better)

Return EXACT format:

MODEL_NAME:
Faithfulness: X
Relevance: X
Coherence: X
Hallucination: X
Toxicity: X

(repeat for all models)

Winner:
Reason:
"""

    response = judge_client.invoke(judge_prompt)

    return response.content