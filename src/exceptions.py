class TaxEngineError(Exception):
    """Base exception for the Tax Engine."""
    pass

class InvalidInputError(TaxEngineError):
    """Raised when the input provided is invalid."""
    pass
