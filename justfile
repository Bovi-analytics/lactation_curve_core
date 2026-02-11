run-milkbot:
    cd apps/milkbot && uv run uvicorn main:app --reload

build-wheel:
    cd packages/python/lactation && uv build

build-app:
    cd packages/python/infrastructure && just build-app

preview-infra:
    cd packages/python/infrastructure && just preview

deploy-infra:
    cd packages/python/infrastructure && just deploy
