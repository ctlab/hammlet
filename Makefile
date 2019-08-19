VERSION := $(shell git describe --tags --long --first-parent --match '*.*' | python -c 's = input(); t,n,_ = s.split("-", 2); n=int(n); v = t; v += f".post{n}" if n > 0 else ""; print(v)')
VERSION_FILE = src/hammlet/version.py

default:
	@echo "Specify a target!"

install: | ensure_version bump_version poentry_install zero_version

build: | ensure_version bump_version poetry_build zero_version

release: | ensure_version bump_version poetry_build poetry_publish zero_version

poentry_install:
	@echo "Installing..."
	@poetry install

poetry_build:
	@echo "Building..."
	@poetry build

poetry_publish:
	@echo "Publishing..."
	poetry publish -r local || true

ensure_version:
	@echo "Writing version '$(VERSION)' to '$(VERSION_FILE)'..."
	@echo -e "# THIS FILE IS GENERATED\nversion = '$(VERSION)'" > "$(VERSION_FILE)"

bump_version:
	@poetry version "$(VERSION)"

zero_version:
	@poetry version '0.0.0'

show_version:
	@echo "Version: '$(VERSION)'"
