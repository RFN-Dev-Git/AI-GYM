.PHONY: all run code

EXERCISE ?= hack_squat
VIDEO ?= hackw.mp4

run:
	clear
	uv run python -m src.main $(EXERCISE) assets/videos/$(VIDEO)

code:
	./codex -e .py

help:
	@echo "  run   - Run the specified exercise with the given video."
	@echo "          Usage: make run EXERCISE=<exercise_name> VIDEO=<video_file>"
	@echo "  code  - Run the code generation tool."
	@echo "  help  - Display this help message."

h: help
