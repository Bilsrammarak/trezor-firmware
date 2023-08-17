/*
 * This file is part of the Trezor project, https://trezor.io/
 *
 * Copyright (c) SatoshiLabs
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "fonts.h"
#include <stdbool.h>

// TODO: make it return uint32_t (needs logic to assemble at most 4 bytes
// together)
static uint16_t convert_char_utf8(const uint8_t c) {
  // Considering only two-byte UTF-8 characters currently
  static uint8_t first_ut8_byte = 0;

  // non-printable ASCII character
  if (c < ' ') {
    first_ut8_byte = 0;
    return 0x7F;
  }

  // regular ASCII character
  if (c < 0x80) {
    first_ut8_byte = 0;
    return c;
  }

  // UTF-8 handling: https://en.wikipedia.org/wiki/UTF-8#Encoding

  // bytes 11xxxxxx are first bytes of UTF-8 characters
  if (c >= 0xC0) {
    first_ut8_byte = c;
    return 0;  // not print this
  }

  if (first_ut8_byte) {
    // encountered a successive UTF-8 character ...
    return ((uint16_t)first_ut8_byte << 8) | c;
  } else {
    // ... or they are just non-printable ASCII characters
    return 0x7F;
  }
}

int font_height(int font) {
  switch (font) {
#ifdef TREZOR_FONT_NORMAL_ENABLE
    case FONT_NORMAL:
      return FONT_NORMAL_HEIGHT;
#endif
#ifdef TREZOR_FONT_DEMIBOLD_ENABLE
    case FONT_DEMIBOLD:
      return FONT_DEMIBOLD_HEIGHT;
#endif
#ifdef TREZOR_FONT_BOLD_ENABLE
    case FONT_BOLD:
      return FONT_BOLD_HEIGHT;
#endif
#ifdef TREZOR_FONT_MONO_ENABLE
    case FONT_MONO:
      return FONT_MONO_HEIGHT;
#endif
#ifdef TREZOR_FONT_BIG_ENABLE
    case FONT_BIG:
      return FONT_BIG_HEIGHT;
#endif
  }
  return 0;
}

int font_max_height(int font) {
  switch (font) {
#ifdef TREZOR_FONT_NORMAL_ENABLE
    case FONT_NORMAL:
      return FONT_NORMAL_MAX_HEIGHT;
#endif
#ifdef TREZOR_FONT_DEMIBOLD_ENABLE
    case FONT_DEMIBOLD:
      return FONT_DEMIBOLD_MAX_HEIGHT;
#endif
#ifdef TREZOR_FONT_BOLD_ENABLE
    case FONT_BOLD:
      return FONT_BOLD_MAX_HEIGHT;
#endif
#ifdef TREZOR_FONT_MONO_ENABLE
    case FONT_MONO:
      return FONT_MONO_MAX_HEIGHT;
#endif
#ifdef TREZOR_FONT_BIG_ENABLE
    case FONT_BIG:
      return FONT_BIG_MAX_HEIGHT;
#endif
  }
  return 0;
}

int font_baseline(int font) {
  switch (font) {
#ifdef TREZOR_FONT_NORMAL_ENABLE
    case FONT_NORMAL:
      return FONT_NORMAL_BASELINE;
#endif
#ifdef TREZOR_FONT_DEMIBOLD_ENABLE
    case FONT_DEMIBOLD:
      return FONT_DEMIBOLD_BASELINE;
#endif
#ifdef TREZOR_FONT_BOLD_ENABLE
    case FONT_BOLD:
      return FONT_BOLD_BASELINE;
#endif
#ifdef TREZOR_FONT_MONO_ENABLE
    case FONT_MONO:
      return FONT_MONO_BASELINE;
#endif
#ifdef TREZOR_FONT_BIG_ENABLE
    case FONT_BIG:
      return FONT_BIG_BASELINE;
#endif
  }
  return 0;
}

const uint8_t utf8_mapping(uint16_t c_2bytes) {
  switch (c_2bytes) {
    case 0xC381:
      return 127;  // Á
    case 0xC48C:
      return 128;  // Č
    case 0xC48E:
      return 129;  // Ď
    case 0xC389:
      return 130;  // É
    case 0xC49A:
      return 131;  // Ě
    case 0xC38D:
      return 132;  // Í
    case 0xC587:
      return 133;  // Ň
    case 0xC393:
      return 134;  // Ó
    case 0xC598:
      return 135;  // Ř
    case 0xC5A0:
      return 136;  // Š
    case 0xC5A4:
      return 137;  // Ť
    case 0xC39A:
      return 138;  // Ú
    case 0xC5AE:
      return 139;  // Ů
    case 0xC39D:
      return 140;  // Ý
    case 0xC5BD:
      return 141;  // Ž
    case 0xC3A1:
      return 142;  // á
    case 0xC48D:
      return 143;  // č
    case 0xC48F:
      return 144;  // ď
    case 0xC3A9:
      return 145;  // é
    case 0xC49B:
      return 146;  // ě
    case 0xC3AD:
      return 147;  // í
    case 0xC588:
      return 148;  // ň
    case 0xC3B3:
      return 149;  // ó
    case 0xC599:
      return 150;  // ř
    case 0xC5A1:
      return 151;  // š
    case 0xC5A5:
      return 152;  // ť
    case 0xC3BA:
      return 153;  // ú
    case 0xC5AF:
      return 154;  // ů
    case 0xC3BD:
      return 155;  // ý
    case 0xC5BE:
      return 156;  // ž
    default:
      return 0;  // nonprintable
  }
}

const uint8_t *font_get_glyph(int font, uint8_t c) {
  uint16_t c_2bytes = convert_char_utf8(c);
  bool is_printable = c_2bytes != 0x7F;
  if (!c_2bytes) return 0;

  // found UTF8 character
  if (c_2bytes > 0xFF) {
    c_2bytes = utf8_mapping(c_2bytes);
    if (!c_2bytes) {
      is_printable = false;
    }
  }

  // printable character
  // TODO: take the 156 as a constant from all the fonts
  if (is_printable && c_2bytes >= ' ' && c_2bytes <= 156) {
    switch (font) {
#ifdef TREZOR_FONT_NORMAL_ENABLE
      case FONT_NORMAL:
        return FONT_NORMAL_DATA[c_2bytes - ' '];
#endif
#ifdef TREZOR_FONT_DEMIBOLD_ENABLE
      case FONT_DEMIBOLD:
        return FONT_DEMIBOLD_DATA[c_2bytes - ' '];
#endif
#ifdef TREZOR_FONT_BOLD_ENABLE
      case FONT_BOLD:
        return FONT_BOLD_DATA[c_2bytes - ' '];
#endif
#ifdef TREZOR_FONT_MONO_ENABLE
      case FONT_MONO:
        return FONT_MONO_DATA[c_2bytes - ' '];
#endif
#ifdef TREZOR_FONT_BIG_ENABLE
      case FONT_BIG:
        return FONT_BIG_DATA[c_2bytes - ' '];
#endif
    }
    return 0;
  }

// non-printable character
#define PASTER(s) s##_glyph_nonprintable
#define NONPRINTABLE_GLYPH(s) PASTER(s)

  switch (font) {
#ifdef TREZOR_FONT_NORMAL_ENABLE
    case FONT_NORMAL:
      return NONPRINTABLE_GLYPH(FONT_NORMAL_DATA);
#endif
#ifdef TREZOR_FONT_DEMIBOLD_ENABLE
    case FONT_DEMIBOLD:
      return NONPRINTABLE_GLYPH(FONT_DEMIBOLD_DATA);
#endif
#ifdef TREZOR_FONT_BOLD_ENABLE
    case FONT_BOLD:
      return NONPRINTABLE_GLYPH(FONT_BOLD_DATA);
#endif
#ifdef TREZOR_FONT_MONO_ENABLE
    case FONT_MONO:
      return NONPRINTABLE_GLYPH(FONT_MONO_DATA);
#endif
  }
  return 0;
}
