.PHONY: fmt lint test build publish clean

fmt:
	uv run ruff format .
	uv run ruff check --fix .

lint:
	uv run ruff check .
	uv run ruff format --check .

test: lint
	uv run pytest --ignore=data


build:
	uv build

publish: clean build
	uv publish

clean:
	rm -rf dist/ build/ *.egg-info .ruff_cache/ .pytest_cache/


