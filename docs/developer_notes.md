# Developer notes

## Interactive tests

Oxymoron similar to "holidays with kids". Since some of these tests are interactive, they're hardly that inviting to run with every change. The issue here is that proper testing of some of the functionality requires developer to be logged in to the service.

### How to run tests

Install the package first, either through `pip install -e .` or with `PyPI`.

Run the `pytest`:

```bash
pytest tests/ -s
```  
The `-s` switch allows for interactive user input.

