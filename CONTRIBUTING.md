# Contributing

Please feel free to contribute to this project. Adding common functions is the intent and if you have one to add or improve an existing it is greatly appreciated.

## Ways to Contribute

- Add or improve a function
- Add or improve documentation
- Add or improve tests
- Report or fix a bug

## Testing Workflow

- Run `make tests` before opening or updating a pull request.
- `tests/test_form_data_parsing.py` is a required regression suite and is run explicitly in local `make tests` and CI workflows.
- Keep this suite passing when changing nested form parsing or assignment behavior.
