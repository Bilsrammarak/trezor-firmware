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
#include "optiga_commands.h"

bool optiga_sign(uint8_t index, const uint8_t *digest, size_t digest_size,
                 uint8_t *signature, size_t max_sig_size, size_t *sig_size) {
  optiga_result ret =
      optiga_calc_sign(0xE0F0 + index, digest, digest_size, &signature[2],
                       max_sig_size - 2, sig_size);
  if (OPTIGA_SUCCESS != ret) {
    return false;
  }

  // Add sequence tag and length.
  if (*sig_size >= 0x80) {
    // Length not supported.
    return false;
  }
  signature[0] = 0x30;
  signature[1] = *sig_size;
  *sig_size += 2;
  return true;
}

bool optiga_cert_size(uint8_t index, size_t *cert_size) {
  *cert_size = 0;

  uint8_t metadata_bytes[258] = {0};
  size_t metadata_size = 0;
  optiga_metadata metadata = {0};
  optiga_result ret =
      optiga_get_data_object(0xE0E0 + index, true, metadata_bytes,
                             sizeof(metadata_bytes), &metadata_size);
  if (OPTIGA_SUCCESS != ret) {
    return false;
  }

  ret = optiga_parse_metadata(metadata_bytes, metadata_size, &metadata);
  if (OPTIGA_SUCCESS != ret || metadata.used_size.ptr == NULL) {
    return false;
  }

  for (int i = 0; i < metadata.used_size.len; ++i) {
    *cert_size = (*cert_size << 8) + metadata.used_size.ptr[i];
  }

  return true;
}

bool optiga_read_cert(uint8_t index, uint8_t *cert, size_t max_cert_size,
                      size_t *cert_size) {
  optiga_result ret = optiga_get_data_object(0xE0E0 + index, false, cert,
                                             max_cert_size, cert_size);
  return OPTIGA_SUCCESS == ret;
}