# Run the lactation_curves FastAPI app locally (default)
run:
    cd apps/lactation_curves && uv run python -m uvicorn main:app --reload

# Run the milkbot FastAPI app locally
run-milkbot:
    cd apps/milkbot && uv run python -m uvicorn main:app --reload

# Run API integration tests against a running local server
test-api:
    cd apps/lactation_curves && uv run pytest tests/ -v

# Run all library-level tests
test:
    uv run pytest tests/ -v

# Build the lactationcurve wheel
build:
    cd packages/python/lactation && uv build

# Publish the lactationcurve package to PyPI
publish:
    #!/usr/bin/env bash
    set -euo pipefail
    set -a && source .env && set +a
    rm -rf packages/python/lactation/dist
    cd packages/python/lactation && uv build && uv publish

# Build app for deployment
build-app:
    cd packages/python/infrastructure && just build-app

# Preview infrastructure changes
preview-infra:
    cd packages/python/infrastructure && just preview

# Deploy infrastructure + function code
deploy-infra:
    cd packages/python/infrastructure && just deploy

# Deploy lactation_curves function code only
deploy-functions:
    cd packages/python/infrastructure && just deploy-functions

# Deploy milkbot function code only
deploy-functions-milkbot:
    cd packages/python/infrastructure && just deploy-functions-milkbot
