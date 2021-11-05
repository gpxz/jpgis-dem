.PHONY: black isort fmt venv

black:
	black --target-version py38 jpgisdem setup.py


isort:
	isort --profile black --project jpgisdem ./jpgisdem

fmt: isort black


