.PHONY: install-dev test build release-check

install-dev:
	python -m pip install --upgrade pip
	python -m pip install -e .[dev]

test:
	python -m pytest

build:
	python -m pip install --upgrade pip
	python -m pip install build
	python -m build

release-check: install-dev test build
