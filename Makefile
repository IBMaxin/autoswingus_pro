.PHONY: bootstrap install test data paper lint fmt

bootstrap:
	@./scripts/bootstrap.sh

install:
	@pip install -r requirements.txt

lint:
	@ruff check .

fmt:
	@ruff check --fix . && ruff format .

test:
	@pytest -q

HIST ?= 1y
SYMS ?= AAPL,MSFT,SPY

data:
	@python -m autoswing.cli data_fetch --symbols $(SYMS) --history $(HIST)

paper:
	@python -m autoswing.cli paper_run
