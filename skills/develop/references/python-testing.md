# Python tests: pytest, test first

pytest is the default for every Python project, new or old. Take the project's existing layout and markers first.
The rules below follow roboflow/rf-detr `AGENTS.md` ("Testing Principles") and `.github/CONTRIBUTING.md`
("Test-Driven Development"), read at commit `5b22dfc` of `develop`.

## The loop

- **Bug fix:** write a test that reproduces it and watch it fail for the right reason; make the minimal fix; run
  the whole suite. The failing test may sit in its own WIP commit; the final commit before a pull request has every
  test passing.
- **New feature:** write tests for all major use cases, including edge cases and invalid input; implement; refactor
  with the tests green.
- **Refactor:** pin behaviour first (`refactor.md`).

## Writing tests

- Group related tests in a class (`class TestModelInference:`). One behaviour per test.
- Never loop over cases inside one test. Use `@pytest.mark.parametrize` so each case is its own test and a failure
  names the case.
- Use bare strings, numbers, booleans and `None` as parameters. Use `pytest.param(..., id="name")` only for a
  function, object or compound setup passed as one case, a per-case mark, or a value whose generated ID would be
  empty or unclear. Do not keep a parallel `ids` list.
- Fixtures return ready-to-use state (a value, or a cohesive tuple), not a factory, unless the fixture must manage a
  lifecycle; use an ordinary helper function for configurable construction. Keep fixture dependencies few.
- Use `tmp_path` for files, `monkeypatch` for environment and attributes. A test never depends on test order,
  network or the clock. Seed anything random.
- Mark GPU or heavy tests `@pytest.mark.gpu`; CPU runs select `-m "not gpu"`. A test that needs an optional extra
  carries `@pytest.mark.integration` and the project's `e2e_<extra>` marker, registered in `pyproject.toml`.
- Never `pytest.importorskip`, and do not `pytest.skip()` for a missing package. Gate with a named
  `pytest.mark.skipif(not _IS_X_INSTALLED, ...)` from the project's imports module and import the package inside the
  test. A broken install should fail, not skip.
- Numbers: compare with `pytest.approx` or `numpy.testing.assert_allclose` and a stated tolerance.
- `assert` belongs in tests only; library code raises (PY-ERR-1 in the style catalogue).

## Running

```
pytest -m "not gpu" --timeout=240 -x -q      # fast loop; add -n auto if pytest-xdist is installed
pytest --cov=<package> --durations=20         # before a pull request
pre-commit run --all-files                    # before every commit, if the project uses pre-commit
```

Use the command the project's CI runs when it differs. Pin `pytest` and its plugins in the dev requirements.
