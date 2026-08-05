from typing import List

def count_tokens(text: str) -> int:
    return len(text.split())

def prune_text_to_tokens(text: str, max_tokens: int) -> str:
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text
    return " ".join(tokens[-max_tokens:])

def trim_history(history: List[str], max_tokens: int) -> List[str]:
    trimmed = []
    running = 0
    for entry in reversed(history):
        entry_tokens = len(entry.split())
        if running + entry_tokens > max_tokens:
            break
        trimmed.append(entry)
        running += entry_tokens
    return list(reversed(trimmed))
