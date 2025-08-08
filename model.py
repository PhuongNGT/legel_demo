def get_model_name(key: str) -> str:
    mapping = {
        "mistral": "mistralai/mistral-7b-instruct:free",
        "llama3": "meta-llama/llama-3-8b-instruct:free",
        "gpt-3.5": "openai/gpt-3.5-turbo-0613"
    }
    if key not in mapping:
        raise ValueError(f"❌ Unknown model key '{key}'. Available keys: {list(mapping.keys())}")
    return mapping[key]
