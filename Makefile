VERSION = $(shell dunamai from git --no-metadata)
VERSION_FILE = src/hammlet/version.py

.PHONY: default build ensure_version

default:
	@echo "Specify a target!"

build: | ensure_version bump_version poetry_build zero_version

poetry_build:
	@echo "Building..."
	@poetry build

release: build
	@echo "Publishing..."
	poetry publish -r local

ensure_version:
	@echo "Writing version '$(VERSION)' to '$(VERSION_FILE)'..."
	@echo -e "# THIS FILE IS GENERATED\nversion = '$(VERSION)'" > $(VERSION_FILE)

bump_version:
	@poetry version $(VERSION)

zero_version:
	@poetry version '0.0.0'
