.DEFAULT_GOAL := help

.PHONY: checklist deploy-checklist help

checklist:
	python3 scripts/generate_checklist.py

deploy-checklist: checklist
	@git worktree add .worktrees/gh-pages gh-pages 2>/dev/null || true; \
	trap 'git worktree remove --force .worktrees/gh-pages 2>/dev/null || true' EXIT; \
	mkdir -p .worktrees/gh-pages/checklist && \
	cp docs/checklist/index.html .worktrees/gh-pages/checklist/index.html && \
	cd .worktrees/gh-pages && \
	git add checklist/index.html && \
	(git diff --cached --quiet && echo "Nothing to deploy — checklist is up to date." || \
		(git commit -m "regen checklist" && git push origin gh-pages))

help:
	@echo ""
	@echo "\033[2mContent\033[0m"
	@echo "  \033[36mchecklist\033[0m         Regenerate docs/checklist/index.html locally"
	@echo ""
	@echo "\033[2mDeploy\033[0m"
	@echo "  \033[36mdeploy-checklist\033[0m  Push checklist to gh-pages (use if CI is unavailable)"
	@echo ""
