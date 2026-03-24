URL     ?=
OUTPUT  ?=
ENGINE  ?= auto
CONFIG  ?=
SPLIT   ?= 0

install:
	pip install -e .

run: ## Scrape a book (e.g. make run URL=https://... OUTPUT=output/book/book.txt SPLIT=1)
	bookworm scrape "$(URL)" -o "$(OUTPUT)" -e $(ENGINE) $(if $(filter-out 0,$(SPLIT)),--split-chapters)

run-resume: ## Resume scraping from config (e.g. make run-resume CONFIG=output/book/bookworm_config.json)
	bookworm resume "$(CONFIG)"

format:
	ruff check --fix .
	ruff format .

f: format

.PHONY: install run run-resume format f
