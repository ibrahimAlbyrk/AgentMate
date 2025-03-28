class RetryException(Exception):
    def __init__(self, last_exception: Exception, attempts: int):
        self.attempts = attempts
        self.last_exception = last_exception
        message = f"Retry failed after {attempts} attempts. Last error: {str(last_exception)}"
        super().__init__(message)
