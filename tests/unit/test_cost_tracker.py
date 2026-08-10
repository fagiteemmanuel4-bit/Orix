import os
import shutil
import tempfile
import pytest
from pathlib import Path
from orix.core.cost_tracker import CostTracker
from orix.core.ai_providers import get_provider

def test_cost_tracker_logging():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracker = CostTracker(tmp_dir)

        # Log mock transaction
        tracker.log_transaction("openai", "gpt-4o-mini", 1000, 500)

        summary = tracker.get_summary()
        assert summary["transactions_count"] == 1
        assert summary["total_input_tokens"] == 1000
        assert summary["total_output_tokens"] == 500
        # gpt-4o-mini: 0.15/1M input, 0.60/1M output
        # expected input cost = 0.00015, output cost = 0.0003
        expected_cost = 0.00015 + 0.0003
        assert pytest.approx(summary["total_cost"], rel=1e-5) == expected_cost

        # Test clear
        tracker.clear()
        summary_clear = tracker.get_summary()
        assert summary_clear["transactions_count"] == 0
