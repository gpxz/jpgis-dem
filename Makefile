.PHONY: black isort fmt


black:
	black --target-version py38 jpgisdem setup.py tests


isort:
	isort --profile black --project jpgisdem ./jpgisdem ./tests


fmt: isort black

test: 
	pytest --ignore=data


