import tiktoken

from Core.config import settings

class TokenEstimator:
    def __init__(self, model_name: str = "gpt-4.1-mini"):
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))