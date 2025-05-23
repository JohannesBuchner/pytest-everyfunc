.PHONY: clean clean-test clean-pyc clean-build docs servedocs help install release release-test dist 
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

PYTHON := python3

BROWSER := $(PYTHON) -c "$$BROWSER_PYSCRIPT"

help:
	@$(PYTHON) -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc clean-test clean-doc ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*.pyx.py' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '*.so' -exec rm -f {} +

clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr .pytest_cache

clean-doc:
	rm -rf docs/build

SOURCES := $(shell ls pytest_everyfunc/*.py)

lint: ${SOURCES} ## check style
	flake8 ${SOURCES}
	pycodestyle ${SOURCES}
	pydocstyle ${SOURCES}

test: ## run tests quickly with the default Python
	PYTHONPATH=. pytest

test-all: ## run tests on every Python version with tox
	tox

build:
	$(PYTHON) setup.py build_ext --inplace

coverage: ## check code coverage quickly with the default Python
	PYTHONPATH=. coverage run --source pytest_everyfunc -m pytest
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docs: ## generate Sphinx HTML documentation, including API docs
	rm -f docs/pytest_everyfunc.rst
	rm -f docs/modules.rst
	rm -f docs/API.rst
	python3 setup.py build_ext --inplace
	sphinx-apidoc -H API -o docs/ pytest_everyfunc
	cd docs; python3 modoverview.py
	$(MAKE) -C docs clean
	$(MAKE) -C docs html O=-jauto
	$(BROWSER) docs/build/html/index.html

servedocs: docs ## compile the docs watching for changes
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release-test: install

release: release-test dist ## package and upload a release
	twine upload --verbose dist/*.tar.gz

dist: clean ## builds source and wheel package
	$(PYTHON) -m pip wheel --no-deps .
	$(PYTHON) -m build
	ls -l dist

install: clean ## install the package to the active Python's site-packages
	$(PYTHON) -m pip install --user .

