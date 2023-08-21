from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent

cs_file = HERE / "cs.json"
en_file = HERE / "en.json"
missing_file = HERE / "missing.json"


# checks that both files have the exact same keys
def get_all_json_keys(data: dict[str, dict[str, str]]) -> set[str]:
    keys: set[str] = set()
    for section_name, section in data.items():
        for k, _v in section.items():
            keys.add(f"{section_name}__{k}")
    return keys


if __name__ == "__main__":
    cs_data = json.loads(cs_file.read_text())
    en_data = json.loads(en_file.read_text())
    cs_keys = get_all_json_keys(cs_data)
    en_keys = get_all_json_keys(en_data)
    if cs_keys == en_keys:
        print("SUCCESS: cs and en files have the same keys")
        exit(0)
    else:
        print("cs and en files have different keys")
        print("cs - en:", len(cs_keys - en_keys))
        print("en - cs:", len(en_keys - cs_keys))
        missing_cs = en_keys - cs_keys
        missing_dict: dict[str, dict[str, str]] = {}
        for missing in sorted(missing_cs):
            section_name, key = missing.split("__")
            if section_name not in missing_dict:
                missing_dict[section_name] = {}
            missing_dict[section_name][key] = en_data[section_name][key]
        missing_file.write_text(json.dumps(missing_dict, indent=4))
        print(f"Diff written into {missing_file}")
        exit(1)
