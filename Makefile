VERSION := $(shell git describe --tags --long --first-parent --match '*.*' | python -c 's = input(); t,n,_ = s.split("-", 2); n=int(n); v = t; v += f".post{n}" if n > 0 else ""; print(v)')
VERSION_FILE = src/hammlet/version.py

default:
	@echo "Specify a target!"

install: | bump_version poentry_install zero_version

build: | bump_version poetry_build zero_version

release: | bump_version poetry_build poetry_publish zero_version

poentry_install:
	@echo "Installing..."
	@poetry install

poetry_build:
	@echo "Building..."
	@poetry build

poetry_publish:
	@echo "Publishing..."
	@poetry publish -r local || true

bump_version:
	@echo "Writing version '$(VERSION)' to '$(VERSION_FILE)'..."
	@echo -e "# THIS FILE IS GENERATED\nversion = '$(VERSION)'" > "$(VERSION_FILE)"
	@poetry version "$(VERSION)"

zero_version:
	@echo "Zeroing version..."
	@poetry version '0.0.0'
	rm -f "$(VERSION_FILE)"

show_version:
	@echo "Version: '$(VERSION)'"
