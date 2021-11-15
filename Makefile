.PHONY: black isort fmt test pypi


black:
	black --target-version py38 jpgisdem setup.py tests


isort:
	isort --profile black --project jpgisdem ./jpgisdem ./tests


fmt: isort black


test: 
	pytest --ignore=data


pypi:
	python setup.py sdist bdist_wheel
	python -m twine upload dist/*


