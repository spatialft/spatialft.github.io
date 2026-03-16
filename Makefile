.DEFAULT_GOAL := help

.PHONY: index benchmark generate deploy colab-pat export-lm-arena check-bootstrap help

GITHUB_COLAB_PAT_URL := https://github.com/settings/personal-access-tokens/new?name=SpatialFT%20Colab&description=Colab%20token%20for%20spatialft.github.io&target_name=spatialft&expires_in=30&contents=write

index:
	@cp -f results/comparison.png docs/assets/comparison.png 2>/dev/null || true
	@cp -f results/finetuned/loss_curve.png docs/assets/loss-curve.png 2>/dev/null || true
	python3 scripts/generate_index.py

benchmark:
	python3 scripts/generate_benchmark.py

generate: index benchmark

# NOTE: `make deploy` pushes to the gh-pages branch. This only works if GitHub
# Pages is configured to deploy from the gh-pages branch (not GitHub Actions).
# The normal CI path (deploy.yml) uses GitHub Actions deployment — the two
# configurations are mutually exclusive. Only use `make deploy` if you have
# temporarily switched the Pages source setting in the repo settings.
deploy: generate
	@git worktree add .worktrees/gh-pages gh-pages 2>/dev/null || true; \
	trap 'git worktree remove --force .worktrees/gh-pages 2>/dev/null || true' EXIT; \
	mkdir -p .worktrees/gh-pages/assets && \
	cp docs/index.html .worktrees/gh-pages/index.html && \
	cp docs/benchmark.html .worktrees/gh-pages/benchmark.html && \
	cp -r docs/assets/. .worktrees/gh-pages/assets/ && \
	cd .worktrees/gh-pages && \
	git add index.html benchmark.html assets/ && \
	(git diff --cached --quiet && echo "Nothing to deploy — site is up to date." || \
		(git commit -m "regen site" && git push origin gh-pages))

colab-pat:
	@url='$(GITHUB_COLAB_PAT_URL)'; \
	if command -v open >/dev/null 2>&1; then \
		open "$$url"; \
	elif command -v xdg-open >/dev/null 2>&1; then \
		xdg-open "$$url"; \
	else \
		printf '%s\n' "$$url"; \
	fi
	@echo "GitHub will still ask you to confirm repository access. Select spatialft.github.io, create the token, then save it in Colab secrets as GITHUB_TOKEN."

# Verify all notebooks share the same bootstrap logic (clone/path block before imports)
check-bootstrap:
	@python3 scripts/check_bootstrap.py

export-lm-arena:
	python3 scripts/export_lm_arena_model.py $(ARGS)

help:
	@echo ""
	@echo "\033[2mContent\033[0m"
	@echo "  \033[36mindex\033[0m      Regenerate docs/index.html"
	@echo "  \033[36mbenchmark\033[0m  Regenerate docs/benchmark.html"
	@echo "  \033[36mgenerate\033[0m   Regenerate both"
	@echo ""
	@echo "  \033[36mcheck-bootstrap\033[0m  Verify notebook bootstrap cells haven't drifted"
	@echo ""
	@echo "\033[2mDeploy\033[0m"
	@echo "  \033[36mdeploy\033[0m     Push full site to gh-pages (fallback if CI unavailable)"
	@echo "  \033[36mcolab-pat\033[0m  Open the fine-grained GitHub PAT form for Colab publishing"
	@echo "  \033[36mexport-lm-arena\033[0m Export merged/GGUF weights for lm-arena. Pass ARGS='...'."
	@echo ""
