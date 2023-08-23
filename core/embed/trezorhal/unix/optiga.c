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

#include "optiga.h"
#include <string.h>
#include "ecdsa.h"
#include "nist256p1.h"

static const uint8_t DEVICE_CERT[] = {
    0x30, 0x82, 0x01, 0x9a, 0x30, 0x82, 0x01, 0x40, 0xa0, 0x03, 0x02, 0x01,
    0x02, 0x02, 0x04, 0x43, 0x59, 0x94, 0xff, 0x30, 0x0a, 0x06, 0x08, 0x2a,
    0x86, 0x48, 0xce, 0x3d, 0x04, 0x03, 0x02, 0x30, 0x4f, 0x31, 0x0b, 0x30,
    0x09, 0x06, 0x03, 0x55, 0x04, 0x06, 0x13, 0x02, 0x43, 0x5a, 0x31, 0x1e,
    0x30, 0x1c, 0x06, 0x03, 0x55, 0x04, 0x0a, 0x0c, 0x15, 0x54, 0x72, 0x65,
    0x7a, 0x6f, 0x72, 0x20, 0x43, 0x6f, 0x6d, 0x70, 0x61, 0x6e, 0x79, 0x20,
    0x73, 0x2e, 0x72, 0x2e, 0x6f, 0x2e, 0x31, 0x20, 0x30, 0x1e, 0x06, 0x03,
    0x55, 0x04, 0x03, 0x0c, 0x17, 0x54, 0x72, 0x65, 0x7a, 0x6f, 0x72, 0x20,
    0x4d, 0x61, 0x6e, 0x75, 0x66, 0x61, 0x63, 0x74, 0x75, 0x72, 0x69, 0x6e,
    0x67, 0x20, 0x43, 0x41, 0x30, 0x1e, 0x17, 0x0d, 0x32, 0x30, 0x30, 0x39,
    0x31, 0x30, 0x31, 0x31, 0x34, 0x30, 0x32, 0x34, 0x5a, 0x17, 0x0d, 0x34,
    0x30, 0x30, 0x39, 0x31, 0x30, 0x31, 0x31, 0x34, 0x30, 0x32, 0x34, 0x5a,
    0x30, 0x18, 0x31, 0x16, 0x30, 0x14, 0x06, 0x03, 0x55, 0x04, 0x03, 0x0c,
    0x0d, 0x54, 0x72, 0x65, 0x7a, 0x6f, 0x72, 0x20, 0x53, 0x61, 0x66, 0x65,
    0x20, 0x33, 0x30, 0x59, 0x30, 0x13, 0x06, 0x07, 0x2a, 0x86, 0x48, 0xce,
    0x3d, 0x02, 0x01, 0x06, 0x08, 0x2a, 0x86, 0x48, 0xce, 0x3d, 0x03, 0x01,
    0x07, 0x03, 0x42, 0x00, 0x04, 0x9b, 0xbf, 0x06, 0xda, 0xd9, 0xab, 0x59,
    0x05, 0xe0, 0x54, 0x71, 0xce, 0x16, 0xd5, 0x22, 0x2c, 0x89, 0xc2, 0xca,
    0xa3, 0x9f, 0x26, 0x26, 0x7a, 0xc0, 0x74, 0x71, 0x29, 0x88, 0x5f, 0xbd,
    0x44, 0x1b, 0xcc, 0x7f, 0xa8, 0x4d, 0xe1, 0x20, 0xa3, 0x67, 0x55, 0xda,
    0xf3, 0x0a, 0x6f, 0x47, 0xe8, 0xc0, 0xd4, 0xbd, 0xdc, 0x15, 0x03, 0x6e,
    0xd2, 0xa3, 0x44, 0x7d, 0xfa, 0x7a, 0x1d, 0x3e, 0x88, 0xa3, 0x41, 0x30,
    0x3f, 0x30, 0x0e, 0x06, 0x03, 0x55, 0x1d, 0x0f, 0x01, 0x01, 0xff, 0x04,
    0x04, 0x03, 0x02, 0x00, 0x80, 0x30, 0x0c, 0x06, 0x03, 0x55, 0x1d, 0x13,
    0x01, 0x01, 0xff, 0x04, 0x02, 0x30, 0x00, 0x30, 0x1f, 0x06, 0x03, 0x55,
    0x1d, 0x23, 0x04, 0x18, 0x30, 0x16, 0x80, 0x14, 0xa4, 0x5f, 0xea, 0x7a,
    0xba, 0xa4, 0x15, 0xde, 0xff, 0xd1, 0x9a, 0xa0, 0x3f, 0xf1, 0x00, 0xa9,
    0xdc, 0x89, 0xff, 0x52, 0x30, 0x0a, 0x06, 0x08, 0x2a, 0x86, 0x48, 0xce,
    0x3d, 0x04, 0x03, 0x02, 0x03, 0x48, 0x00, 0x30, 0x45, 0x02, 0x21, 0x00,
    0xd6, 0x12, 0x3d, 0xed, 0x0c, 0x04, 0xb0, 0xab, 0x66, 0x64, 0x9f, 0x4b,
    0xa0, 0x0c, 0x3f, 0xcf, 0x8e, 0x2c, 0xab, 0xe1, 0x0f, 0xb4, 0x3b, 0xfa,
    0x93, 0xf3, 0x4b, 0xcc, 0x3b, 0xe6, 0x9f, 0x4d, 0x02, 0x20, 0x2d, 0x08,
    0xff, 0x01, 0xba, 0x22, 0x72, 0x25, 0x93, 0x54, 0xe5, 0x79, 0xeb, 0x5f,
    0x07, 0x9d, 0xaf, 0xec, 0xe3, 0xe2, 0x00, 0x64, 0x0c, 0x63, 0xf8, 0x00,
    0xdb, 0x02, 0x7d, 0xe9, 0x59, 0xec};

bool optiga_sign(uint8_t index, const uint8_t *digest, size_t digest_size,
                 uint8_t *signature, size_t max_sig_size, size_t *sig_size) {
  const uint8_t DEVICE_PRIV_KEY[32] = {1};
  if (max_sig_size < 72) {
    return false;
  }

  uint8_t raw_signature[64] = {0};
  int ret = ecdsa_sign_digest(&nist256p1, DEVICE_PRIV_KEY, digest,
                              raw_signature, NULL, NULL);
  if (ret != 0) {
    return false;
  }

  *sig_size = ecdsa_sig_to_der(raw_signature, signature);
  return true;
}

bool optiga_cert_size(uint8_t index, size_t *cert_size) {
  *cert_size = sizeof(DEVICE_CERT);
  return true;
}

bool optiga_read_cert(uint8_t index, uint8_t *cert, size_t max_cert_size,
                      size_t *cert_size) {
  if (max_cert_size < sizeof(DEVICE_CERT)) {
    return false;
  }

  memcpy(cert, DEVICE_CERT, sizeof(DEVICE_CERT));
  *cert_size = sizeof(DEVICE_CERT);
  return true;
}
