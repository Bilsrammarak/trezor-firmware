import json
from pathlib import Path
from typing import Any, Iterable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

UPY_TRANSLATIONS = ROOT / "core" / "src" / "trezor" / "translations"
RUST_TRANSLATIONS = ROOT / "core" / "embed" / "rust" / "src" / "ui" / "translations"

LANGUAGES = ["cs", "en"]


def _get_all_language_data() -> list[dict[str, dict[str, str]]]:
    return [_get_language_data(language) for language in LANGUAGES]


def _get_language_data(language: str) -> dict[str, dict[str, str]]:
    upy_file = UPY_TRANSLATIONS / f"{language}.json"
    rust_file = RUST_TRANSLATIONS / f"{language}.json"
    upy_data = json.loads(upy_file.read_text())
    rust_data = json.loads(rust_file.read_text())

    # Merge the dictionaries in a way to not overwrite top-level keys
    all_keys = set(rust_data.keys()) | set(upy_data.keys())
    merged_data: dict[str, dict[str, str]] = {}
    for key in all_keys:
        merged_data[key] = {**rust_data.get(key, {}), **upy_data.get(key, {})}
    return merged_data


all_language_data = _get_all_language_data()


def _resolve_path_to_texts(path: str, template: Iterable[Any] = ()) -> list[str]:
    texts: list[str] = []
    lookups = path.split(".")
    for language_data in all_language_data:
        data: dict[str, Any] | str = language_data
        for lookup in lookups:
            assert isinstance(data, dict), f"{lookup} is not a dict"
            data = data[lookup]
        assert isinstance(data, str), f"{path} is not a string"
        if template:
            data = data.format(*template)
        texts.append(data)
    return texts


def assert_equals(text: str, path: str, template: Iterable[Any] = ()) -> None:
    texts = _resolve_path_to_texts(path, template)
    assert text in texts, f"{text} not found in {texts}"


def assert_in(text: str, path: str, template: Iterable[Any] = ()) -> None:
    texts = _resolve_path_to_texts(path, template)
    for t in texts:
        if t in text:
            return
    assert False, f"{text} not found in {texts}"


def assert_startswith(text: str, path: str, template: Iterable[Any] = ()) -> None:
    texts = _resolve_path_to_texts(path, template)
    for t in texts:
        if text.startswith(t):
            return
    assert False, f"{text} not found in {texts}"


def translate(path: str, template: Iterable[Any] = ()) -> list[str]:
    return _resolve_path_to_texts(path, template)
