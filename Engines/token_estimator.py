import tiktoken

class TokenEstimator:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.encoder = tiktoken.encoding_for_model(model_name)

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))