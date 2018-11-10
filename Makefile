.PHONY: clean data jupyter lint requirements venv

#################################################################################
# GLOBALS                                                                       #
#################################################################################
PROJECT_NAME = ev-simulation
PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
VENV_DIR =  $(PROJECT_DIR)/env
# JUPYTER_DIR =  $(VENV_DIR)/share/jupyter

PYTHON_INTERPRETER = $(VENV_DIR)/bin/python3
PIP = $(VENV_DIR)/bin/pip
# IPYTHON = $(VENV_DIR)/bin/ipython
# JUPYTER = $(VENV_DIR)/bin/jupyter

# NOTEBOOK_DIR =  $(PROJECT_DIR)/notebooks

#################################################################################
# COMMANDS                                                                      #
#################################################################################
## Simulation
simulate:
	$(PYTHON_INTERPRETER) simulation.py

example:
	$(PYTHON_INTERPRETER) example.py


## Install Python Dependencies
requirements: venv
	$(PIP) install -U pip setuptools wheel
	$(PIP) install -r requirements.txt

## Make Dataset
data:
	# @$(PYTHON_INTERPRETER) src/$(PROJECT_NAME)/data/make_dataset.py

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Lint using flake8
lint:
	@$(PYTHON_INTERPRETER) -m flake8 --config=$(PROJECT_DIR)/.flake8 simulation.py

## Install virtual environment
venv:
ifeq ($(wildcard $(VENV_DIR)/*),)
	@echo "Did not find $(VENV_DIR), creating..."
	mkdir -p $(VENV_DIR)
	python3 -m venv $(VENV_DIR)
endif

