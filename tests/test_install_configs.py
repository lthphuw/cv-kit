from pathlib import Path

import pytest

from install_configs import ASSETS, FILES, install, main


def test_every_listed_asset_exists():
    for lang, files in FILES.items():
        for rel in files:
            assert (ASSETS / lang / rel).is_file(), f"{lang}/{rel}"


def test_copies_python_and_cpp_configs(tmp_path):
    copied, skipped, held = install(tmp_path, ["cpp", "python"])
    assert sorted(copied) == sorted(FILES["cpp"] + FILES["python"])
    assert (skipped, held) == ([], {})
    assert (tmp_path / "cmake/cv_kit_strict.cmake").read_bytes() == (ASSETS / "cpp/cmake/cv_kit_strict.cmake").read_bytes()


def test_existing_file_is_kept_unless_forced(tmp_path):
    (tmp_path / ".clang-format").write_text("BasedOnStyle: LLVM\n", encoding="utf-8")
    _, skipped, _ = install(tmp_path, ["cpp"])
    assert skipped == [".clang-format"]
    assert (tmp_path / ".clang-format").read_text(encoding="utf-8") == "BasedOnStyle: LLVM\n"
    copied, _, _ = install(tmp_path, ["cpp"], force=True)
    assert ".clang-format" in copied


@pytest.mark.parametrize(("name", "text", "held"), [
    ("pyproject.toml", "[project]\nname = 'x'\n\n[tool.ruff]\nline-length = 100\n", "ruff.toml"),
    ("pyproject.toml", "[tool.ruff.lint]\nselect = ['E']\n", "ruff.toml"),
    (".ruff.toml", "line-length = 100\n", "ruff.toml"),
    ("pyproject.toml", "[tool.mypy]\nstrict = false\n", "mypy.ini"),
    ("setup.cfg", "[metadata]\nname = x\n\n[mypy]\nstrict = False\n", "mypy.ini"),
])
def test_another_config_for_the_same_tool_holds_ours_back(tmp_path, name, text, held):
    (tmp_path / name).write_text(text, encoding="utf-8")
    copied, _, found = install(tmp_path, ["python"], force=True)
    assert found == {held: name}
    assert held not in copied and not (tmp_path / held).exists()


def test_unrelated_pyproject_does_not_hold_back(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n# [tool.ruff] lives elsewhere\n", encoding="utf-8")
    copied, _, held = install(tmp_path, ["python"])
    assert held == {} and "ruff.toml" in copied


def test_symlinked_cmake_directory_is_refused_and_nothing_is_written(tmp_path):
    project = tmp_path / "proj"
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    project.mkdir()
    (project / "cmake").symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(ValueError, match="refusing to write through a symlink"):
        install(project, ["cpp"])
    assert list(elsewhere.iterdir()) == [] and not (project / ".clang-format").exists()


def test_main_reports_held_back_files(tmp_path, capsys):
    (tmp_path / "pyproject.toml").write_text("[tool.ruff]\n", encoding="utf-8")
    assert main([str(tmp_path), "--lang", "python"]) == 0
    out = capsys.readouterr().out
    assert "not copied: ruff.toml (the project configures this tool in pyproject.toml" in out
    assert "copied: mypy.ini" in out


def test_main_needs_a_language(tmp_path):
    with pytest.raises(SystemExit):
        main([str(tmp_path)])


def test_main_rejects_a_missing_project(tmp_path, capsys):
    assert main([str(tmp_path / "nope"), "--lang", "cpp"]) == 1
    assert "not a directory" in capsys.readouterr().err


def test_files_are_relative_and_inside_the_project():
    for files in FILES.values():
        for rel in files:
            assert not Path(rel).is_absolute() and ".." not in Path(rel).parts
