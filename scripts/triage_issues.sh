#!/usr/bin/env bash
# Historical helper from the 2026 issue cleanup.
# Issues #9 and #10 were closed then. #11, #12, #14, and #16 are implemented
# in the codebase; close them from GitHub after the implementation is pushed.

set -euo pipefail

echo "No remaining scripted closes. Current open issues:"
gh issue list --repo adamsimms/driftwood --state open
