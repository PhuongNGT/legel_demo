def get_model_name(key: str) -> str:
    mapping = {
        "mistral": "mistralai/mistral-7b-instruct",
        "llama3": "meta-llama/llama-3-8b-instruct",
        "gpt-3.5": "openai/gpt-3.5-turbo-0613"
    }
    return mapping[key]

