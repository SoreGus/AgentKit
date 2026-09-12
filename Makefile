-include .env
export

PYTHON_BIN ?= python3.14
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python

.PHONY: all setup clean

all: setup

setup:
	@echo "Using Python: $(PYTHON_BIN)"
	@$(PYTHON_BIN) --version
	@$(PYTHON_BIN) -m venv $(VENV)
	@$(VENV_PYTHON) -m pip install --upgrade pip
	@$(VENV_PYTHON) -m pip install -e .
	@echo ""
	@echo "AgentKit environment ready."
	@echo "Activate it with: source $(VENV)/bin/activate"

clean:
	rm -rf $(VENV)
