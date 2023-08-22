#include <stdint.h>

#if TREZOR_FONT_BPP != 4
#error Wrong TREZOR_FONT_BPP (expected 4)
#endif
#define Font_TTHoves_Bold_17_HEIGHT 17
#define Font_TTHoves_Bold_17_MAX_HEIGHT 21
#define Font_TTHoves_Bold_17_BASELINE 4
extern const uint8_t* const Font_TTHoves_Bold_17[156 + 1 - 32];
extern const uint8_t Font_TTHoves_Bold_17_glyph_nonprintable[];
