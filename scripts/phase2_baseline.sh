#!/bin/bash
# PHASE 2: Clean-Room Baseline Testing for Orix
# Execute this script to validate installation and test status

set -e  # Exit on error

VENV_DIR=".venv"
TEST_OUTPUT="phase2_baseline_report.txt"

{
    echo "========================================"
    echo "ORIX X P0.5 CLEAN-ROOM BASELINE TEST"
    echo "========================================"
    echo "Date: $(date)"
    echo "Python: $(python3 --version)"
    echo "Current Directory: $(pwd)"
    echo ""

    # Step 1: Check existing venv
    if [ -d "$VENV_DIR" ]; then
        echo "[STEP 1] Using existing venv at $VENV_DIR"
        source "$VENV_DIR/bin/activate"
    else
        echo "[STEP 1] Creating fresh venv..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
    fi

    # Step 2: Upgrade pip
    echo "[STEP 2] Upgrading pip, setuptools, wheel..."
    pip install --quiet --upgrade pip setuptools wheel

    # Step 3: Install Orix
    echo "[STEP 3] Installing Orix from current directory (pip install -e .)..."
    if pip install -e . 2>&1; then
        echo "✅ Installation successful"
    else
        echo "❌ Installation failed - see error above"
    fi

    # Step 4: List installed packages
    echo ""
    echo "[STEP 4] Installed packages (relevant):"
    pip list | grep -E "(orix|click|rich|questionary|pytest|jinja|yaml|requests)" || echo "  (none found)"

    # Step 5: Test CLI version
    echo ""
    echo "[STEP 5] CLI Version Test:"
    if orix --version 2>&1; then
        echo "✅ orix --version works"
    else
        echo "❌ orix --version failed"
    fi

    # Step 6: Test CLI help
    echo ""
    echo "[STEP 6] CLI Help Test (first 30 lines):"
    orix --help 2>&1 | head -30 || echo "❌ orix --help failed"

    # Step 7: Install test dependencies
    echo ""
    echo "[STEP 7] Installing pytest..."
    pip install --quiet pytest pytest-cov

    # Step 8: Import tests
    echo ""
    echo "[STEP 8] Import Tests:"
    
    echo -n "  - orix.core.cli: "
    python3 -c "from orix.core.cli import cli; print('✅')" 2>&1 || echo "❌"
    
    echo -n "  - orix.core.toolbox: "
    python3 -c "from orix.core.toolbox import WorkspaceToolbox; print('✅')" 2>&1 || echo "❌"
    
    echo -n "  - orix.core.permissions: "
    python3 -c "from orix.core.permissions import PermissionManager; print('✅')" 2>&1 || echo "❌"
    
    echo -n "  - orix.core.indexer: "
    python3 -c "from orix.core.indexer import WorkspaceIndexer; print('✅')" 2>&1 || echo "❌"
    
    echo -n "  - orix.core.agent: "
    python3 -c "from orix.core.agent import AgentSession; print('✅')" 2>&1 || echo "❌"
    
    echo -n "  - orix.core.forge: "
    python3 -c "from orix.core.forge import ForgeWorkflow; print('✅')" 2>&1 || echo "❌"
    
    echo -n "  - orix.core.doctor: "
    python3 -c "from orix.core.doctor import OrixDoctor; print('✅')" 2>&1 || echo "❌"

    # Step 9: Run pytest
    echo ""
    echo "[STEP 9] Running pytest (full output):"
    echo "=========================================="
    pytest -v --tb=short 2>&1 || true
    echo "=========================================="

    # Step 10: Test summary
    echo ""
    echo "[STEP 10] Test Summary:"
    pytest --co -q 2>&1 | tail -3 || echo "(could not get test count)"

    # Step 11: Check for common issues
    echo ""
    echo "[STEP 11] Common Issue Checks:"
    
    if [ -f "orix/core/vector_store.py" ] && [ -f "orix/core/simple_vector_store.py" ] && [ -f "orix/core/keyword_store.py" ]; then
        echo "  ⚠️  WARNING: Multiple vector store implementations found!"
        echo "    - vector_store.py exists"
        echo "    - simple_vector_store.py exists"
        echo "    - keyword_store.py exists"
        echo "    This may cause import conflicts."
    fi

    if ! grep -q "py.typed" setup.py 2>/dev/null && ! ls -la orix/py.typed 2>/dev/null | grep -q py.typed; then
        echo "  ⚠️  WARNING: py.typed marker file missing (PEP 561 violation)"
    fi

    if [ ! -f "orix/__init__.py" ]; then
        echo "  ⚠️  WARNING: orix/__init__.py missing (implicit namespace package)"
    fi

    echo ""
    echo "========================================"
    echo "PHASE 2 BASELINE COMPLETE"
    echo "========================================"

} | tee "$TEST_OUTPUT"

echo ""
echo "📋 Full report saved to: $TEST_OUTPUT"
echo ""
echo "Next steps:"
echo "  1. Review the report above"
echo "  2. Note any ❌ failures"
echo "  3. Check for ⚠️  warnings"
echo "  4. Share the output with the hardening team"
