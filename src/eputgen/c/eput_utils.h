#ifndef EPUT_UTILS
#define EPUT_UTILS

#include <stdint.h>
#include <stddef.h>

#define TLV_TYPE_NULL 0x00
#define TLV_TYPE_TERMINATOR 0xFE
#define TLV_TYPE_NDEF 0x03

#define TNF_URI   0x03
#define RECORD_TYPE_SCHEME "https://pma.inftech.hs-mannheim.de/eput"

#define SUCCESS 0
#define ERR_NO_NDEF_TLV -10
#define ERR_REC_BUF_TRUNCATED -20
#define ERR_REC_WRONG_TYPE -21
#define ERR_DATA_BUF_WRONG_LENGTH -30

typedef int64_t time_point;
typedef int16_t zone_offset;

typedef struct {
    time_point time;
    zone_offset offset;
} zoned_time;

typedef struct {
    uint8_t hours;
    uint8_t minutes;
    uint8_t seconds;
} hh_mm_ss;

typedef struct {
    hh_mm_ss from;
    hh_mm_ss to;
} time_range;

typedef struct {
    time_point from;
    time_point to;
} date_range;

// val = unscaled * 10 ^ -scale
typedef struct {
    int32_t unscaled;
    int32_t scale;
} fixp32;

// val = unscaled * 10 ^ -scale
typedef struct {
    int64_t unscaled;
    int32_t scale;
} fixp64;

typedef struct {
    uint8_t tnf;
    uint8_t type_length;
    uint8_t *type;
    uint8_t id_length;
    uint8_t *id;
    uint32_t payload_length;
    uint8_t *payload;
} ndef_record;

uint8_t bytes_to_uint8(uint8_t *bytes);
uint16_t bytes_to_uint16(uint8_t *bytes);
uint32_t bytes_to_uint32(uint8_t *bytes);
uint64_t bytes_to_uint64(uint8_t *bytes);
int8_t bytes_to_int8(uint8_t *bytes);
int16_t bytes_to_int16(uint8_t *bytes);
int32_t bytes_to_int32(uint8_t *bytes);
int64_t bytes_to_int64(uint8_t *bytes);

void uint8_to_bytes(uint8_t val, uint8_t *bytes);
void uint16_to_bytes(uint16_t val, uint8_t *bytes);
void uint32_to_bytes(uint32_t val, uint8_t *bytes);
void uint64_to_bytes(uint64_t val, uint8_t *bytes);
void int8_to_bytes(int8_t val, uint8_t *bytes);
void int16_to_bytes(int16_t val, uint8_t *bytes);
void int32_to_bytes(int32_t val, uint8_t *bytes);
void int64_to_bytes(int64_t val, uint8_t *bytes);

float bytes_to_float(uint8_t *bytes);
double bytes_to_double(uint8_t *bytes);
void float_to_bytes(float val, uint8_t *bytes);
void double_to_bytes(double val, uint8_t *bytes);

uint8_t bytes_to_bool(uint8_t *bytes);
void bool_to_bytes(uint8_t val, uint8_t *bytes);

time_point bytes_to_time_point(uint8_t *bytes);
void time_point_to_bytes(time_point val, uint8_t *bytes);
hh_mm_ss bytes_to_hh_mm_ss(uint8_t *bytes);
void hh_mm_ss_to_bytes(hh_mm_ss val, uint8_t *bytes);
date_range bytes_to_date_range(uint8_t *bytes);
void date_range_to_bytes(date_range val, uint8_t *bytes);
time_range bytes_to_time_range(uint8_t *bytes);
void time_range_to_bytes(time_range val, uint8_t *bytes);
zone_offset bytes_to_zone_offset(uint8_t *bytes);
void zone_offset_to_bytes(zone_offset val, uint8_t *bytes);
zoned_time bytes_to_zoned_time(uint8_t *bytes);
void zoned_time_to_bytes(zoned_time val, uint8_t *bytes);

fixp32 bytes_to_fixp32(uint8_t *bytes, int32_t scale);
void fixp32_to_bytes(fixp32 val, uint8_t *bytes);
fixp64 bytes_to_fixp64(uint8_t *bytes, int32_t scale);
void fixp64_to_bytes(fixp64 val, uint8_t *bytes);

/**
 * @brief Get index and length of value field of first NDEF TLV in `buf`.
 * 
 * Start of NDEF message is marked by TLV of type ndef.
 * Need to go through memory until this TLV is encountered.
 * 
 * @param buf pointer to buffer
 * @param buf_len length of `buf`
 * @param offset_p pointer to store index to
 * 
 * @return length of value field if bigger than 0, otherwise TLV not found or truncated buffer
 **/
uint16_t get_ndef_tlv_offset(
    uint8_t *buf,
    size_t buf_len,
    size_t *offset_p);

/**
 * @brief Extract NDEF record contents from buffer, assuming `buf` points to start of record.
 * 
 * @param buf pointer to NDEF record buffer
 * @param buf_len length of `buf`
 * @param record pointer to store record to
 * 
 * @return length of extracted record in `buf` if bigger than 0, otherwise error code
 **/
int get_record(uint8_t *buf, size_t buf_len, ndef_record *record);

/**
 * @brief Extract meta data and data records from buffer containing NDEF message.
 * 
 * @param buf pointer to NDEF message buffer
 * @param buf_len length of `buf`
 * @param meta_rec pointer to store meta data record to
 * @param data_rec pointer to store data record to
 * 
 * @return status code
 **/
int get_records(
    uint8_t *buf,
    size_t buf_len,
    ndef_record *meta_rec,
    ndef_record *data_rec);

/**
 * @brief Determine wether bit with index `option` is set in bitmap.
 * 
 * @param bitmap pointer to bitmap buffer
 * @param bitmap_len length of `bitmap`
 * @param option index of bit to check
 * 
 * @return `1` if bit is set, otherwise `0`
 **/
uint8_t is_option_selected(uint8_t* bitmap, size_t bitmap_len, uint8_t option);

#endif
