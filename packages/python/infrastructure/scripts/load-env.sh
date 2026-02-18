#!/usr/bin/env bash
# Load Pulumi environment variables from .env files.
# Source this script from justfile recipes:  source scripts/load-env.sh
set -euo pipefail

CURRENT_STACK=$(pulumi stack --show-name)

if [[ ! -f .env ]]; then
    echo "Error: .env file not found! Run 'just configure' first."
    exit 1
fi

set -a
source .env
[[ -f ".env.${CURRENT_STACK}" ]] && source ".env.${CURRENT_STACK}"
set +a

export PULUMI_CONFIG_PASSPHRASE
