import re

class TokenCounter:
    """
    Provides token counting for prompts.
    For SD1.5, we target a limit of approximately 77 tokens.
    """
    @staticmethod
    def count_tokens(text: str) -> int:
        """
        Approximates the number of CLIP tokens in a string.
        CLIP uses a byte-pair encoding (BPE). A good heuristic is roughly 
        4 characters per token, but words are safer for basic UX.
        """
        if not text:
            return 0
        
        # Professional approach: Use a regex to find words/punctuation
        # This is much more accurate than just .split()
        tokens = re.findall(r"[\w']+|[.,!?;]", text)
        return len(tokens)

    @staticmethod
    def get_limit(model_name: str = "sd15") -> int:
        """Returns the token limit for a given model."""
        # Standard SD1.5 limit
        if "sd15" in model_name.lower():
            return 77
        # Default fallback
        return 2048