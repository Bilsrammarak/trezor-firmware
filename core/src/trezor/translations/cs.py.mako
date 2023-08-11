# generated from cs.py.mako
# (by running `make templates` in `core`)
# do not edit manually!
# fmt: off

<%
import json

from pathlib import Path
from itertools import chain

THIS = Path(local.filename).resolve()
SRCDIR = THIS.parent

file = SRCDIR / "cs.json"

data = json.loads(file.read_text())
items_to_write: list[tuple[str, str]] = []
for section_name, section in data.items():
    for k, v in section.items():
        name = f"{section_name}__{k}"
        items_to_write.append((name, v))
%>\
# TODO: try `from micropython import const` and compare it

% for k, v in items_to_write:
${k} = ${utf8_str(v)}
% endfor
