//! generated from cs.rs.mako
//! (by running `make templates` in `core`)
//! do not edit manually!

// TODO: try the same with traits and consts
// trait Translations {
//    const VALUE1:  &'static str;
//    const VALUE2: &'static str;
// }
// struct EnTranslations;
// impl Translations for EnTranslations {
//     const VALUE1: &'static str = "Hello";
//     const VALUE2: &'static str = "World!";
// }

<%
import json
from pathlib import Path

THIS = Path(local.filename).resolve()
SRCDIR = THIS.parent

cs_file = SRCDIR / "cs.json"
en_file = SRCDIR / "en.json"

cs_data = json.loads(cs_file.read_text())
en_data = json.loads(en_file.read_text())

# checks that both files have the exact same keys
def get_all_json_keys(data: dict) -> set[str]:
    keys: set[str] = set()
    for section_name, section in data.items():
        for k, v in section.items():
            keys.add(f"{section_name}__{k}")
    return keys

cs_keys = get_all_json_keys(cs_data)
en_keys = get_all_json_keys(en_data)
if cs_keys != en_keys:
    raise ValueError("cs.json and en.json have different keys")
%>\
#[allow(non_snake_case)]
pub struct TranslationsGeneral {
% for name in sorted(cs_keys):
    pub ${name}: &'static str,
% endfor
}
