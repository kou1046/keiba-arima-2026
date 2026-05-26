.PHONY: sync lint test fmt \
	scrape-weekly backfill-stakes backfill-nakayama backfill-horses brief-upcoming brief-review

# 依存解決 (uv)
sync:
	uv sync --extra dev

lint:
	uv run ruff check src tests

fmt:
	uv run ruff format src tests

test:
	uv run pytest -q

# --- jobs (それぞれ GH Actions workflow からも同じ entrypoint を叩く) ---
scrape-weekly:
	uv run python -m keiba_arima.jobs.scrape_weekly

backfill-stakes:
	uv run python -m keiba_arima.jobs.backfill_stakes

backfill-nakayama:
	uv run python -m keiba_arima.jobs.backfill_nakayama

backfill-horses:
	uv run python -m keiba_arima.jobs.backfill_horses

brief-upcoming:
	uv run python -m keiba_arima.jobs.brief_upcoming

brief-review:
	uv run python -m keiba_arima.jobs.brief_review
