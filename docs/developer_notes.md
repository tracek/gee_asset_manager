# Developer notes

## Interactive tests

Oxymoron similar to "holidays with kids". Since some of these tests are interactive, they're hardly that inviting to run with every change. The issue here is that proper testing of some of the functionality requires developer to be logged in to the service.

### Run the tests

Install the package first, either through `pip install -e .` or with `PyPI`.

Run the `pytest`:

```bash
pytest tests/ -s
```  
The `-s` switch allows for interactive user input.

## Build & publish the package

Build:
```bash
python setup.py sdist bdist_wheel
```

Test deployment:

```bash
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

