from __future__ import annotations

czech_chars = [
    ("Á", "0xC381"),
    ("Č", "0xC48C"),
    ("Ď", "0xC48E"),
    ("É", "0xC389"),
    ("Ě", "0xC49A"),
    ("Í", "0xC38D"),
    ("Ň", "0xC587"),
    ("Ó", "0xC393"),
    ("Ř", "0xC598"),
    ("Š", "0xC5A0"),
    ("Ť", "0xC5A4"),
    ("Ú", "0xC39A"),
    ("Ů", "0xC5AE"),
    ("Ý", "0xC39D"),
    ("Ž", "0xC5BD"),
    ("á", "0xC3A1"),
    ("č", "0xC48D"),
    ("ď", "0xC48F"),
    ("é", "0xC3A9"),
    ("ě", "0xC49B"),
    ("í", "0xC3AD"),
    ("ň", "0xC588"),
    ("ó", "0xC3B3"),
    ("ř", "0xC599"),
    ("š", "0xC5A1"),
    ("ť", "0xC5A5"),
    ("ú", "0xC3BA"),
    ("ů", "0xC5AF"),
    ("ý", "0xC3BD"),
    ("ž", "0xC5BE"),
]

if __name__ == "__main__":
    # Generating a C function for getting the index from utf8 value
    template = """\
const uint8_t utf8_mapping(uint16_t c_2bytes) {
  switch (c_2bytes) {
XXXXXXXXXXXXXXXXXXXX
    default: return 0; // non-printable
  }
}
"""
    lines: list[str] = []
    for index, (key, value) in enumerate(czech_chars):
        line = f"    case {value}: return {127 + index}; // {key}"
        lines.append(line)
    function = template.replace("XXXXXXXXXXXXXXXXXXXX", "\n".join(lines))
    print(function)
