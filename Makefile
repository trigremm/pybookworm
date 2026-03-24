install:
	pip install -e .

format:
	ruff check --fix .
	ruff format .

f: format

.PHONY: install format f
