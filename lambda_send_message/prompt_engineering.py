def gen_prompt_from_chat_history(history, question):
    """
    Generate a prompt for LLM from chat history and a new user question.

    Parameters:
    - history: List of tuples (user_message, bot_response)
    - question: A string representing the new user question

    Returns:
    - A formatted prompt string
    """
    prompt = "You are a useful assistant, the following is a conversation between a user and you.\n"
    for i, msg in enumerate(history):
        if i % 2 == 0:
            prompt += f"User: {msg}\n"
        else:
            prompt += f"Assistant: {msg}\n"
    prompt += f"Now please answer user's question: {question}\n"
    return prompt
