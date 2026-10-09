.PHONY: build serve clean
PYTHON ?= python3

build:
	$(PYTHON) site/build-site.py

# Local preview only. The intranet web server can serve dist/ directly.
serve: build
	$(PYTHON) -m http.server 8848 --bind 127.0.0.1 --directory dist

clean:
	rm -rf dist
