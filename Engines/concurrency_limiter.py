from Engines.token_estimator import TokenEstimator

class ConcurrencyLimiter:
    def __init__(self, token_limit_per_minute: int = 90000, model: str = "gpt-4.1-nano"):
        self.token_limit_per_minute = token_limit_per_minute
        self.estimator = TokenEstimator(model)

    def calculate_max_concurrent_tasks(self, texts: list[str]) -> int:
        token_counts = [self.estimator.count_tokens(t) for t in texts]
        total_estimate = sum(token_counts)
        avg_estimate = total_estimate / max(len(token_counts), 1)

        max_tasks = self.token_limit_per_minute // max(avg_estimate, 1)
        return max(1, min(max_tasks, len(texts)))