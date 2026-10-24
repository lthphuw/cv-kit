---
paths:
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/conftest.py"
  - "tests/**/*.py"
---
# Python tests (pytest)

Follow these when writing or editing Python tests. They come from roboflow/rf-detr's `AGENTS.md` and `CONTRIBUTING.md`; the full guide is `skills/develop/references/python-testing.md` in the cv-kit plugin.

- Write the failing test first and run it to see it fail for the right reason. The final commit before a pull request has every test passing.
- Group related tests in a class. One behaviour per test. Never loop over cases inside a test: use `@pytest.mark.parametrize`.
- Parameters are bare strings, numbers, booleans and `None`. Use `pytest.param(..., id="name")` only for an object or function, a per-case mark, or an unclear generated ID. No parallel `ids` list.
- Fixtures return ready-to-use state, not factories; keep their dependencies few. Use `tmp_path` and `monkeypatch`.
- Mark GPU or heavy tests `@pytest.mark.gpu`. Never `pytest.importorskip`; gate optional dependencies with a named `skipif`.
- Compare floats with `pytest.approx` or `assert_allclose` and a stated tolerance. Seed anything random. No network, clock or test-order dependence.
- Run `pytest -m "not gpu"` and the project's linters before committing.
