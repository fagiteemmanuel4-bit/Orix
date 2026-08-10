import os
import json
from pathlib import Path
from typing import Dict, Any, List

# Pricing per million (1M) tokens in USD
PRICING_REGISTRY = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "llama3": {"input": 0.0, "output": 0.0},
    "mock-model": {"input": 0.0, "output": 0.0}
}

class CostTracker:
    def __init__(self, workspace_root: str):
        self.root = Path(workspace_root).resolve()
        self.tracker_file = self.root / ".orix" / "cost_tracker.json"

    def _ensure_dir(self):
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)

    def load_transactions(self) -> List[Dict[str, Any]]:
        if not self.tracker_file.exists():
            return []
        try:
            with open(self.tracker_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_transactions(self, transactions: List[Dict[str, Any]]):
        self._ensure_dir()
        try:
            with open(self.tracker_file, "w", encoding="utf-8") as f:
                json.dump(transactions, f, indent=2)
        except Exception:
            pass

    def log_transaction(self, provider: str, model: str, input_tokens: int, output_tokens: int):
        pricing = PRICING_REGISTRY.get(model, {"input": 0.0, "output": 0.0})

        # Calculate cost
        input_cost = (input_tokens / 1_000_000.0) * pricing["input"]
        output_cost = (output_tokens / 1_000_000.0) * pricing["output"]
        total_cost = input_cost + output_cost

        transactions = self.load_transactions()
        transactions.append({
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        })
        self.save_transactions(transactions)

    def get_summary(self) -> Dict[str, Any]:
        transactions = self.load_transactions()
        total_input = sum(t.get("input_tokens", 0) for t in transactions)
        total_output = sum(t.get("output_tokens", 0) for t in transactions)
        total_cost = sum(t.get("total_cost", 0.0) for t in transactions)
        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_cost": total_cost,
            "transactions_count": len(transactions),
            "transactions": transactions
        }

    def clear(self):
        if self.tracker_file.exists():
            try:
                self.tracker_file.unlink()
            except Exception:
                pass
