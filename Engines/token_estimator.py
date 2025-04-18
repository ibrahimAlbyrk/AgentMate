import tiktoken

class TokenEstimator:
    def __init__(self, model_name: str = "gpt-4.1-nano"):
        self.encoder = tiktoken.encoding_for_model("gpt-4o-mini")

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))