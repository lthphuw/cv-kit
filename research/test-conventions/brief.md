# Brief: test conventions for cv-kit 0.3

Question: which test rules should the plugin teach agents for Python and C++?

- Python: pytest, following roboflow/rf-detr `AGENTS.md` ("Testing Principles") and `.github/CONTRIBUTING.md`
  ("Test-Driven Development"). Commit in `evidence/repos.json`.
- C++: GoogleTest, following `docs/primer.md`, `docs/advanced.md` and `docs/quickstart-cmake.md`. Commit in
  `evidence/repos.json`.

Result: `skills/develop/references/python-testing.md` and `cpp-testing.md`, `rules/python-tests.md` and
`rules/cpp-tests.md`. Clones are in `repos/` and are not committed.
