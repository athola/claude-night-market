# config/make/docs.mk - Documentation targets
# Requires: common.mk (for HAS_SPHINX, SPHINXBUILD, DOCS_BUILD_DIR, PYTHON variables)

docs: ## Build HTML documentation
ifndef HAS_SPHINX
	$(error sphinx is required for documentation. Install via: uv pip install sphinx sphinx-rtd-theme)
endif
	@echo "Building documentation..."
	@cd docs && $(SPHINXBUILD) -b html source $(@F)

docs-clean: ## Clean documentation build
	@echo "Cleaning documentation..."
	@rm -rf $(DOCS_BUILD_DIR)

docs-serve: ## Serve documentation locally (http://localhost:8000)
	@test -d $(DOCS_BUILD_DIR)/html || { echo "[WARN] Documentation not built. Run 'make docs' first."; exit 1; }
	@echo "Serving documentation at http://localhost:8000"
	@cd $(DOCS_BUILD_DIR)/html && $(PYTHON) -m http.server 8000

docs-check: ## Check documentation links
ifndef HAS_SPHINX
	$(error sphinx is required for documentation. Install via: uv pip install sphinx sphinx-rtd-theme)
endif
	@echo "Checking documentation links..."
	@cd docs && $(SPHINXBUILD) -b linkcheck source build/linkcheck || true
