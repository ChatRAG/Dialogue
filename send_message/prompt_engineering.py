import os
from typing import List, Dict, Any
from google import genai

MAX_TOKENS = 30000

client = genai.Client(api_key=os.environ['GEMINI_KEY'])
client = genai.Client(api_key='AIzaSyAV-GaZr-QCpT0jY_t7wwg3OtY3gQWmKu0')

requirement_prompt = '''
### Requirements
Based on the provided document information and conversation history, answer user questions as required.
**General Requirements:**
- Answering questions should be professional and accurate.
- The answer should be as organized as possible, please divide it into points where necessary. The answer should follow Markdown syntax.
**If the answer to the question cannot be obtained based on the document information, the following requirements must be met:**
- Please try to answer by combining the document information with your own knowledge. Then end the answer.
**If questions can be answered based on document information, the following requirements must be met:**
- Use the information provided in the document to answer the question, and try to match the meaning of the original paragraph as much as possible. It is not allowed to fabricate incorrect answers through divergence and association.
'''


def count_text_tokens(text: str) -> int:
    return client.models.count_tokens(model="gemini-2.0-flash", contents=text).total_tokens


def truncate_chunks_to_token_limit(recalled_chunks: Dict[str, List[Dict[str, Any]]], limit: int) -> List[str]:
    formatted_sections = []
    total_tokens = 0
    i = 1

    for file_key, chunks in recalled_chunks.items():
        chunk0 = chunks[0]
        title = chunk0['title']
        combined_content = "\n".join(chunk["content"] for chunk in chunks)
        section_text = f"<passage[{i}]>\nDocument: {title}\nDocumentFragments: {combined_content}"
        tokens = count_text_tokens(section_text)

        if total_tokens + tokens > limit:
            break

        formatted_sections.append(section_text)
        total_tokens += tokens
        i += 1

    return formatted_sections


def truncate_history_to_token_limit(history: List[str], limit: int) -> List[str]:
    formatted_history = []
    total_tokens = 0

    for i, msg in enumerate(history):
        speaker = "User" if i % 2 == 0 else "Assistant"
        entry = f"{speaker}: {msg}"
        tokens = count_text_tokens(entry)
        if total_tokens + tokens > limit:
            break
        formatted_history.append(entry)
        total_tokens += tokens

    return formatted_history


def truncate_question(question: str, limit: int) -> str:
    while count_text_tokens(question) > limit and len(question) > 10:
        question = question[: int(len(question) * 0.9)]
    return question


def gen_prompt(history: List[str], recalled_chunks: Dict[str, List[Dict[str, Any]]], question: str) -> str:
    token_budget = MAX_TOKENS - count_text_tokens(requirement_prompt)
    rag_budget = int(token_budget * 0.6)
    history_budget = int(token_budget * 0.3)
    question_budget = int(token_budget * 0.1)

    truncated_rag = truncate_chunks_to_token_limit(recalled_chunks, rag_budget)
    truncated_history = truncate_history_to_token_limit(history, history_budget)
    truncated_question = truncate_question(question, question_budget)

    prompt_parts = []

    if truncated_rag:
        prompt_parts.append("### Documents:\n" + "\n\n".join(truncated_rag))
    if truncated_history:
        prompt_parts.append("### Conversation History:\n" + "\n".join(truncated_history))
    prompt_parts.append(requirement_prompt)
    prompt_parts.append("### User Question:\n" + truncated_question)

    return "\n\n".join(prompt_parts)
