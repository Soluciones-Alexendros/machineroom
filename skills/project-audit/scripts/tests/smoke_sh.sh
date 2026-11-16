#!/bin/bash
# Smoke test for project-audit scripts
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Test scan_repo.py
echo "Testing scan_repo.py..."
python3 "$SCRIPT_DIR/scan_repo.py" --help >/dev/null 2>&1 || exit 1
echo "  scan_repo.py --help OK"

# Test audit-repo.sh
echo "Testing audit-repo.sh..."
bash -n "$SCRIPT_DIR/audit-repo.sh" || exit 1
echo "  audit-repo.sh syntax OK"

# Test check-product-structure.sh
echo "Testing check-product-structure.sh..."
bash -n "$SCRIPT_DIR/check-product-structure.sh" || exit 1
"$SCRIPT_DIR/check-product-structure.sh" --help >/dev/null 2>&1 || true
echo "  check-product-structure.sh syntax OK"

# Test inicio_plan.py
echo "Testing inicio_plan.py..."
python3 "$SCRIPT_DIR/inicio_plan.py" --help >/dev/null 2>&1 || exit 1
echo "  inicio_plan.py --help OK"

echo "All smoke tests passed!"