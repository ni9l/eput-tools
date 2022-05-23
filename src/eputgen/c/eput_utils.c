#include "eput_utils.h"
#include <string.h>
#include <stdalign.h>
#include <assert.h>

static inline int is_big_endian() {
    int i = 1;
    return ! *((char *)&i);
}

uint8_t bytes_to_uint8(uint8_t *bytes) {
    return (uint8_t) bytes[0];
}

uint16_t bytes_to_uint16(uint8_t *bytes) {
    return (((uint16_t) bytes[0]) << 8)
         + ((uint16_t) bytes[1]);
}

uint32_t bytes_to_uint32(uint8_t *bytes) {
    return (((uint32_t) bytes[0]) << 24)
         + (((uint32_t) bytes[1]) << 16)
         + (((uint32_t) bytes[2]) << 8)
         + ((uint32_t) bytes[3]);
}

uint64_t bytes_to_uint64(uint8_t *bytes) {
    return (((uint64_t) bytes[0]) << 56)
         + (((uint64_t) bytes[1]) << 48)
         + (((uint64_t) bytes[2]) << 40)
         + (((uint64_t) bytes[3]) << 32)
         + (((uint64_t) bytes[4]) << 24)
         + (((uint64_t) bytes[5]) << 16)
         + (((uint64_t) bytes[6]) << 8)
         + ((uint64_t) bytes[7]);
}

void uint8_to_bytes(uint8_t val, uint8_t *bytes) {
    bytes[0] = (uint8_t) val;
}

void uint16_to_bytes(uint16_t val, uint8_t *bytes) {
    bytes[0] = (uint8_t) (val >> 8);
    bytes[1] = (uint8_t) val;
}

void uint32_to_bytes(uint32_t val, uint8_t *bytes) {
    bytes[0] = (uint8_t) (val >> 24);
    bytes[1] = (uint8_t) (val >> 16);
    bytes[2] = (uint8_t) (val >> 8);
    bytes[3] = (uint8_t) val;
}

void uint64_to_bytes(uint64_t val, uint8_t *bytes) {
    bytes[0] = (uint8_t) (val >> 56);
    bytes[1] = (uint8_t) (val >> 48);
    bytes[2] = (uint8_t) (val >> 40);
    bytes[3] = (uint8_t) (val >> 32);
    bytes[4] = (uint8_t) (val >> 24);
    bytes[5] = (uint8_t) (val >> 16);
    bytes[6] = (uint8_t) (val >> 8);
    bytes[7] = (uint8_t) val;
}

int8_t bytes_to_int8(uint8_t *bytes) {
    return (int8_t) *bytes;
}

int16_t bytes_to_int16(uint8_t *bytes) {
    int16_t i = 0;
    i += bytes[0];
    i <<= (int16_t) 8;
    i += bytes[1];
    return (int16_t) i;
}

int32_t bytes_to_int32(uint8_t *bytes) {
    int32_t i = 0;
    i += bytes[0];
    i <<= (int32_t) 8;
    i += bytes[1];
    i <<= (int32_t) 8;
    i += bytes[2];
    i <<= (int32_t) 8;
    i += bytes[3];
    return (int32_t) i;
}

int64_t bytes_to_int64(uint8_t *bytes) {
    int64_t i = 0;
    i += bytes[0];
    i <<= (int64_t) 8;
    i += bytes[1];
    i <<= (int64_t) 8;
    i += bytes[2];
    i <<= (int64_t) 8;
    i += bytes[3];
    i <<= (int64_t) 8;
    i += bytes[4];
    i <<= (int64_t) 8;
    i += bytes[5];
    i <<= (int64_t) 8;
    i += bytes[6];
    i <<= (int64_t) 8;
    i += bytes[7];
    return (int64_t) i;
}

void int8_to_bytes(int8_t val, uint8_t *bytes) {
    bytes[0] = (uint8_t) val;
}

void int16_to_bytes(int16_t val, uint8_t *bytes) {
    bytes[1] = (uint8_t) val;
    val >>= (int16_t) 8;
    bytes[0] = (uint8_t) val;
}

void int32_to_bytes(int32_t val, uint8_t *bytes) {
    bytes[3] = (uint8_t) val;
    val >>= (int32_t) 8;
    bytes[2] = (uint8_t) val;
    val >>= (int32_t) 8;
    bytes[1] = (uint8_t) val;
    val >>= (int32_t) 8;
    bytes[0] = (uint8_t) val;
}

void int64_to_bytes(int64_t val, uint8_t *bytes) {
    bytes[7] = (uint8_t) val;
    val >>= (int64_t) 8;
    bytes[6] = (uint8_t) val;
    val >>= (int64_t) 8;
    bytes[5] = (uint8_t) val;
    val >>= (int64_t) 8;
    bytes[4] = (uint8_t) val;
    val >>= (int64_t) 8;
    bytes[3] = (uint8_t) val;
    val >>= (int64_t) 8;
    bytes[2] = (uint8_t) val;
    val >>= (int64_t) 8;
    bytes[1] = (uint8_t) val;
    val >>= (int64_t) 8;
    bytes[0] = (uint8_t) val;
}

float bytes_to_float(uint8_t *bytes) {
    static_assert(sizeof(float) == 4, "Float must be 4 bytes");
    // Interpret byte array as float, correct alignment neccessary for cast
    if (is_big_endian()) {
        alignas(alignof(float)) uint8_t b[4] = {bytes[0], bytes[1], bytes[2], bytes[3]};
        return *((float *) b);
    } else {
        alignas(alignof(float)) float i = 0.0;
        alignas(alignof(float)) uint8_t b[4] = {bytes[3], bytes[2], bytes[1], bytes[0]};
        i = *((float *) &b);
        return i;
    }
}

double bytes_to_double(uint8_t *bytes) {
    static_assert(sizeof(double) == 8, "Double must be 8 bytes");
    // Interpret byte array as double, correct alignment neccessary for cast
    if (is_big_endian()) {
        alignas(alignof(double)) uint8_t b[8] = {
            bytes[0],
            bytes[1],
            bytes[2],
            bytes[3],
            bytes[4],
            bytes[5],
            bytes[6],
            bytes[7]};
        return *((double *) b);
    } else {
        alignas(alignof(double)) double i = 0.0;
        alignas(alignof(double)) uint8_t b[8] = {
            bytes[7],
            bytes[6],
            bytes[5],
            bytes[4],
            bytes[3],
            bytes[2],
            bytes[1],
            bytes[0]};
        i = *((double *) &b);
        return i;
    }
}

void float_to_bytes(float val, uint8_t *bytes) {
    static_assert(sizeof(float) == 4, "Float must be 4 bytes");
    uint8_t *p = (uint8_t *) &val;
    if (is_big_endian()) {
        bytes[0] = p[0];
        bytes[1] = p[1];
        bytes[2] = p[2];
        bytes[3] = p[3];
    } else {
        bytes[0] = p[3];
        bytes[1] = p[2];
        bytes[2] = p[1];
        bytes[3] = p[0];
    }
}

void double_to_bytes(double val, uint8_t *bytes) {
    static_assert(sizeof(double) == 8, "Double must be 8 bytes");
    uint8_t *p = (uint8_t *) &val;
    if (is_big_endian()) {
        bytes[0] = p[0];
        bytes[1] = p[1];
        bytes[2] = p[2];
        bytes[3] = p[3];
        bytes[4] = p[4];
        bytes[5] = p[5];
        bytes[6] = p[6];
        bytes[7] = p[7];
    } else {
        bytes[0] = p[7];
        bytes[1] = p[6];
        bytes[2] = p[5];
        bytes[3] = p[4];
        bytes[4] = p[3];
        bytes[5] = p[2];
        bytes[6] = p[1];
        bytes[7] = p[0];
    }
}

uint8_t bytes_to_bool(uint8_t *bytes) {
    return (*bytes) != 0;
}

void bool_to_bytes(uint8_t val, uint8_t *bytes) {
    (*bytes) = val;
}

time_point bytes_to_time_point(uint8_t *bytes) {
    return bytes_to_int64(bytes);
}

void time_point_to_bytes(time_point val, uint8_t *bytes) {
    int64_to_bytes(val, bytes);
}

hh_mm_ss bytes_to_hh_mm_ss(uint8_t *bytes) {
    hh_mm_ss time = {0};
    time.hours = bytes_to_uint8(bytes);
    time.minutes = bytes_to_uint8(bytes + 1);
    time.seconds = bytes_to_uint8(bytes + 2);
    return time;
}

void hh_mm_ss_to_bytes(hh_mm_ss val, uint8_t *bytes) {
    uint8_to_bytes(val.hours, bytes);
    uint8_to_bytes(val.minutes, bytes + 1);
    uint8_to_bytes(val.seconds, bytes + 2);
}

date_range bytes_to_date_range(uint8_t *bytes) {
    date_range range = {0};
    range.from = bytes_to_time_point(bytes);
    range.to = bytes_to_time_point(bytes + sizeof(time_point));
    return range;
}

void date_range_to_bytes(date_range val, uint8_t *bytes) {
    time_point_to_bytes(val.from, bytes);
    time_point_to_bytes(val.to, bytes + sizeof(time_point));
}

time_range bytes_to_time_range(uint8_t *bytes) {
    time_range range = {0};
    range.from = bytes_to_hh_mm_ss(bytes);
    range.to = bytes_to_hh_mm_ss(bytes + 3);
    return range;
}

void time_range_to_bytes(time_range val, uint8_t *bytes) {
    hh_mm_ss_to_bytes(val.from, bytes);
    hh_mm_ss_to_bytes(val.to, bytes + 3);
}

zone_offset bytes_to_zone_offset(uint8_t *bytes) {
    return bytes_to_int16(bytes);
}

void zone_offset_to_bytes(zone_offset val, uint8_t *bytes) {
    int16_to_bytes(val, bytes);
}

zoned_time bytes_to_zoned_time(uint8_t *bytes) {
    zoned_time time = {0};
    time.time = bytes_to_time_point(bytes);
    time.offset = bytes_to_zone_offset(bytes + sizeof(time_point));
    return time;
}

void zoned_time_to_bytes(zoned_time val, uint8_t *bytes) {
    time_point_to_bytes(val.time, bytes);
    zone_offset_to_bytes(val.offset, bytes + sizeof(time_point));
}

fixp32 bytes_to_fixp32(uint8_t *bytes, int32_t scale) {
    fixp32 val = {0};
    val.unscaled = bytes_to_int32(bytes);
    val.scale = scale;
    return val;
}

void fixp32_to_bytes(fixp32 val, uint8_t *bytes) {
    int32_to_bytes(val.unscaled, bytes);
}

fixp64 bytes_to_fixp64(uint8_t *bytes, int32_t scale) {
    fixp64 val = {0};
    val.unscaled = bytes_to_int64(bytes);
    val.scale = scale;
    return val;
}

void fixp64_to_bytes(fixp64 val, uint8_t *bytes) {
    int64_to_bytes(val.unscaled, bytes);
}

// Adapted from https://stackoverflow.com/a/744822
uint8_t ends_with(const char *str, size_t str_len, const char *suffix) {
    if (!str || !suffix) {
        return 0;
    }
    size_t lensuffix = strlen(suffix);
    if (lensuffix >  str_len) {
        return 0;
    }
    return strncmp(str + str_len - lensuffix, suffix, lensuffix) == 0;
}

// Adapted from https://stackoverflow.com/a/744822
uint8_t starts_with(const char *str, size_t str_len, const char *prefix) {
    if (!str || !prefix) {
        return 0;
    }
    size_t prefix_len = strlen(prefix);
    if (prefix_len >  str_len) {
        return 0;
    }
    return strncmp(str, prefix, prefix_len) == 0;
}

uint8_t type_valid(uint8_t *bytes, size_t len) {
    return starts_with((char *) bytes, len, RECORD_TYPE_SCHEME);
}

uint16_t get_ndef_tlv_offset(uint8_t *buf, size_t buf_len, size_t *offset_p) {
    size_t index = 0;
    while (index < buf_len) {
        uint8_t type = buf[index];
        if (type == TLV_TYPE_NULL) {
            index += 1;
            continue;
        } else if (type == TLV_TYPE_TERMINATOR) {
            break;
        } else {
            index += 1;
            uint16_t length = 0;
            if (buf_len < index + 1) {
                break;
            }
            if (buf[index] == 0xFF) {
                // Size is 3 bytes, byte 2 + 3 are actual size
                if (buf_len < index + 2) {
                    break;
                }
                length = (((uint16_t) buf[index + 1]) << 8) + ((uint16_t) buf[index + 2]);
                index += 3;
                if (length == 0xFFFF) {
                    // Value is reserved - treat as invalid
                    break;
                }
            } else {
                // Size is 1 byte
                length = buf[index];
                index += 1;
            }
            if (type == TLV_TYPE_NDEF) {
                *offset_p = index;
                return length;
            } else {
                index += length;
            }
        }
    }
    return 0;
}

int get_record(uint8_t *buf, size_t buf_len, ndef_record *record) {
    uint8_t flags = 0;
    uint8_t *type = NULL;
    uint8_t type_length = 0;
    uint8_t *id = NULL;
    uint8_t id_length = 0;
    uint32_t payload_length = 0;
    uint8_t *payload = NULL;
    
    if (buf_len < 2) {
        return ERR_REC_BUF_TRUNCATED;
    }
    flags = buf[0];
    uint8_t tnf = flags & 0x07;
    uint8_t id_length_present = flags & 0x08;
    uint8_t short_record = flags & 0x10;
    type_length = buf[1];
    if (short_record > 0) {
        payload_length = buf[2];
    } else {
        payload_length = bytes_to_uint32(buf + 2);
    }
    int pl_length = short_record > 0 ? 1 : 4;
    int idl_length = id_length_present > 0 ? 1 : 0;
    if (id_length_present > 0) {
        id_length = buf[2 + pl_length];
        if (id_length > 0) {
            id = buf + 2 + pl_length + idl_length + type_length;
        }
    }
    type = buf + 2 + pl_length + idl_length;
    payload = buf + 2 + pl_length + idl_length + type_length + id_length;

    if (buf_len < 2 + pl_length + idl_length + type_length + id_length + payload_length) {
        return ERR_REC_BUF_TRUNCATED;
    }

    record->tnf = tnf;
    record->type_length = type_length;
    record->type = type;
    record->id_length = id_length;
    record->id = id;
    record->payload_length = payload_length;
    record->payload = payload;
    return 2 + pl_length + idl_length + type_length + id_length + payload_length;
}

int get_records(
    uint8_t *buf,
    size_t buf_len,
    ndef_record *meta_rec,
    ndef_record *data_rec) {
    int ret = get_record(buf, buf_len, data_rec);
    if (ret < 0) {
        return ret;
    } else if (data_rec->tnf != TNF_URI || !type_valid(data_rec->type, data_rec->type_length)) {
        return ERR_REC_WRONG_TYPE;
    }
    ret = get_record(buf + ret, buf_len - ret, meta_rec);
    if (ret < 0) {
        return ret;
    } else if (meta_rec->tnf != TNF_URI || !type_valid(meta_rec->type, meta_rec->type_length)) {
        return ERR_REC_WRONG_TYPE;
    }
    return SUCCESS;
}

uint8_t is_option_selected(uint8_t* bitmap, size_t bitmap_len, uint8_t option) {
    assert(option < (bitmap_len * 8));
    size_t map_index = option / 8;
    size_t byte_index = option % 8;
    uint8_t b = bitmap[map_index];
    uint8_t mask = 0x01 << byte_index;
    return (b & mask) != 0;
}
