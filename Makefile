.DEFAULT_GOAL := help

.PHONY: checklist index generate deploy help

checklist:
	python3 scripts/generate_checklist.py

index:
	python3 scripts/generate_index.py

generate: checklist index

deploy: generate
	@git worktree add .worktrees/gh-pages gh-pages 2>/dev/null || true; \
	trap 'git worktree remove --force .worktrees/gh-pages 2>/dev/null || true' EXIT; \
	mkdir -p .worktrees/gh-pages/checklist && \
	cp docs/checklist/index.html .worktrees/gh-pages/checklist/index.html && \
	cp docs/index.html .worktrees/gh-pages/index.html && \
	cd .worktrees/gh-pages && \
	git add checklist/index.html index.html && \
	(git diff --cached --quiet && echo "Nothing to deploy — site is up to date." || \
		(git commit -m "regen site" && git push origin gh-pages))

help:
	@echo ""
	@echo "\033[2mContent\033[0m"
	@echo "  \033[36mchecklist\033[0m  Regenerate docs/checklist/index.html"
	@echo "  \033[36mindex\033[0m      Regenerate docs/index.html"
	@echo "  \033[36mgenerate\033[0m   Regenerate both"
	@echo ""
	@echo "\033[2mDeploy\033[0m"
	@echo "  \033[36mdeploy\033[0m     Push full site to gh-pages (fallback if CI unavailable)"
	@echo ""
