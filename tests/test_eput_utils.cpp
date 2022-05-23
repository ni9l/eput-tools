#include <gtest/gtest.h>
#include <utility>
#include <vector>
#include <algorithm>

#include <limits>

extern "C" {
    #include "../src/eputgen/c/eput_utils.h"
}

void test_uint8(uint8_t val) {
    uint8_t bytes[1] = {0};
    uint8_to_bytes(val, bytes);
    uint8_t res = bytes_to_uint8(bytes);
    ASSERT_EQ(val, res);
}

void test_uint16(uint16_t val) {
    uint8_t bytes[2] = {0};
    uint16_to_bytes(val, bytes);
    uint16_t res = bytes_to_uint16(bytes);
    ASSERT_EQ(val, res);
}

void test_uint32(uint32_t val) {
    uint8_t bytes[4] = {0};
    uint32_to_bytes(val, bytes);
    uint32_t res = bytes_to_uint32(bytes);
    ASSERT_EQ(val, res);
}

void test_uint64(uint64_t val) {
    uint8_t bytes[8] = {0};
    uint64_to_bytes(val, bytes);
    uint64_t res = bytes_to_uint64(bytes);
    ASSERT_EQ(val, res);
}

void test_int8(int8_t val) {
    uint8_t bytes[1] = {0};
    int8_to_bytes(val, bytes);
    int8_t res = bytes_to_int8(bytes);
    ASSERT_EQ(val, res);
}

void test_int16(int16_t val) {
    uint8_t bytes[2] = {0};
    int16_to_bytes(val, bytes);
    int16_t res = bytes_to_int16(bytes);
    ASSERT_EQ(val, res);
}

void test_int32(int32_t val) {
    uint8_t bytes[4] = {0};
    int32_to_bytes(val, bytes);
    int32_t res = bytes_to_int32(bytes);
    ASSERT_EQ(val, res);
}

void test_int64(int64_t val) {
    uint8_t bytes[8] = {0};
    int64_to_bytes(val, bytes);
    int64_t res = bytes_to_int64(bytes);
    ASSERT_EQ(val, res);
}

void test_float(float val) {
    uint8_t bytes[4] = {0};
    float_to_bytes(val, bytes);
    float res = bytes_to_float(bytes);
    ASSERT_EQ(val, res);
}

void test_double(float val) {
    uint8_t bytes[8] = {0};
    double_to_bytes(val, bytes);
    double res = bytes_to_double(bytes);
    ASSERT_EQ(val, res);
}

void test_bool(bool val) {
    uint8_t bytes[1] = {0};
    bool_to_bytes(val, bytes);
    bool res = bytes_to_bool(bytes);
    ASSERT_EQ(val, res);
}

void test_time_point(time_point val) {
    uint8_t bytes[8] = {0};
    time_point_to_bytes(val, bytes);
    time_point res = bytes_to_time_point(bytes);
    ASSERT_EQ(val, res);
}

void test_hh_mm_ss(hh_mm_ss val) {
    uint8_t bytes[3] = {0};
    hh_mm_ss_to_bytes(val, bytes);
    hh_mm_ss res = bytes_to_hh_mm_ss(bytes);
    ASSERT_EQ(val.hours, res.hours);
    ASSERT_EQ(val.minutes, res.minutes);
    ASSERT_EQ(val.seconds, res.seconds);
}

void test_date_range(date_range val) {
    uint8_t bytes[16] = {0};
    date_range_to_bytes(val, bytes);
    date_range res = bytes_to_date_range(bytes);
    ASSERT_EQ(val.from, res.from);
    ASSERT_EQ(val.to, res.to);
}

void test_time_range(time_range val) {
    uint8_t bytes[6] = {0};
    time_range_to_bytes(val, bytes);
    time_range res = bytes_to_time_range(bytes);
    ASSERT_EQ(val.from.hours, res.from.hours);
    ASSERT_EQ(val.from.minutes, res.from.minutes);
    ASSERT_EQ(val.from.seconds, res.from.seconds);
    ASSERT_EQ(val.to.hours, res.to.hours);
    ASSERT_EQ(val.to.minutes, res.to.minutes);
    ASSERT_EQ(val.to.seconds, res.to.seconds);
}

void test_zone_offset(zone_offset val) {
    uint8_t bytes[2] = {0};
    zone_offset_to_bytes(val, bytes);
    zone_offset res = bytes_to_zone_offset(bytes);
    ASSERT_EQ(val, res);
}

void test_zoned_time(zoned_time val) {
    uint8_t bytes[10] = {0};
    zoned_time_to_bytes(val, bytes);
    zoned_time res = bytes_to_zoned_time(bytes);
    ASSERT_EQ(val.offset, res.offset);
    ASSERT_EQ(val.time, res.time);
}

void test_fixp32(fixp32 val) {
    uint8_t bytes[8] = {0};
    fixp32_to_bytes(val, bytes);
    fixp32 res = bytes_to_fixp32(bytes, val.scale);
    ASSERT_EQ(val.unscaled, res.unscaled);
    ASSERT_EQ(val.scale, res.scale);
}

void test_fixp64(fixp64 val) {
    uint8_t bytes[12] = {0};
    fixp64_to_bytes(val, bytes);
    fixp64 res = bytes_to_fixp64(bytes, val.scale);
    ASSERT_EQ(val.unscaled, res.unscaled);
    ASSERT_EQ(val.scale, res.scale);
}

TEST(eput_utils, uint_conversion) {
    test_uint8(0);
    test_uint8(1);
    test_uint8(UINT8_MAX / 2);
    test_uint8(UINT8_MAX - 1);
    test_uint8(UINT8_MAX);

    test_uint16(0);
    test_uint16(1);
    test_uint16(UINT16_MAX / 2);
    test_uint16(UINT16_MAX - 1);
    test_uint16(UINT16_MAX);

    test_uint32(0);
    test_uint32(1);
    test_uint32(UINT32_MAX / 2);
    test_uint32(UINT32_MAX - 1);
    test_uint32(UINT32_MAX);

    test_uint64(0);
    test_uint64(1);
    test_uint64(UINT64_MAX / 2);
    test_uint64(UINT64_MAX - 1);
    test_uint64(UINT64_MAX);
}

TEST(eput_utils, int_conversion) {
    test_int8(INT8_MIN);
    test_int8(INT8_MIN + 1);
    test_int8(INT8_MIN / 2);
    test_int8(-1);
    test_int8(0);
    test_int8(1);
    test_int8(INT8_MAX / 2);
    test_int8(INT8_MAX - 1);
    test_int8(INT8_MAX);

    test_int16(INT16_MIN);
    test_int16(INT16_MIN + 1);
    test_int16(INT16_MIN / 2);
    test_int16(-1);
    test_int16(0);
    test_int16(1);
    test_int16(INT16_MAX / 2);
    test_int16(INT16_MAX - 1);
    test_int16(INT16_MAX);
    
    test_int32(INT32_MIN);
    test_int32(INT32_MIN + 1);
    test_int32(INT32_MIN / 2);
    test_int32(-1);
    test_int32(0);
    test_int32(1);
    test_int32(INT32_MAX / 2);
    test_int32(INT32_MAX - 1);
    test_int32(INT32_MAX);

    test_int64(INT64_MIN);
    test_int64(INT64_MIN + 1);
    test_int64(INT64_MIN / 2);
    test_int64(-1);
    test_int64(0);
    test_int64(1);
    test_int64(INT64_MAX / 2);
    test_int64(INT64_MAX - 1);
    test_int64(INT64_MAX);
}

TEST(eput_utils, float_conversion) {
    test_float(FLT_MIN);
    test_float(FLT_MIN + 1.5);
    test_float(FLT_MIN / 2.5);
    test_float(-1.5);
    test_float(0.0);
    test_float(1.5);
    test_float(FLT_MAX / 2.5);
    test_float(FLT_MAX - 1.5);
    test_float(FLT_MAX);

    test_double(DBL_MIN);
    test_double(DBL_MIN + 1.5);
    test_double(DBL_MIN / 2.5);
    test_double(-1.5);
    test_double(0.0);
    test_double(1.5);
    test_double(DBL_MAX / 2.5);
    test_double(DBL_MAX - 1.5);
    test_double(DBL_MAX);
}

TEST(eput_utils, time_conversion) {
    test_time_point(INT64_MIN);
    test_time_point(INT64_MIN + 1);
    test_time_point(INT64_MIN / 2);
    test_time_point(-1);
    test_time_point(0);
    test_time_point(1);
    test_time_point(INT64_MAX / 2);
    test_time_point(INT64_MAX - 1);
    test_time_point(INT64_MAX);

    test_hh_mm_ss({0, 0, 0});
    test_hh_mm_ss({0, 0, 1});
    test_hh_mm_ss({0, 1, 0});
    test_hh_mm_ss({1, 0, 0});
    test_hh_mm_ss({0, 1, 1});
    test_hh_mm_ss({1, 1, 0});
    test_hh_mm_ss({1, 1, 1});
    test_hh_mm_ss({0, 0, 30});
    test_hh_mm_ss({0, 30, 0});
    test_hh_mm_ss({12, 0, 0});
    test_hh_mm_ss({0, 30, 30});
    test_hh_mm_ss({12, 30, 0});
    test_hh_mm_ss({12, 30, 30});
    test_hh_mm_ss({0, 0, 59});
    test_hh_mm_ss({0, 59, 0});
    test_hh_mm_ss({23, 0, 0});
    test_hh_mm_ss({0, 59, 59});
    test_hh_mm_ss({23, 59, 0});
    test_hh_mm_ss({23, 59, 59});
    test_hh_mm_ss({0, 0, 60});
    test_hh_mm_ss({0, 60, 0});
    test_hh_mm_ss({24, 0, 0});
    test_hh_mm_ss({0, 60, 60});
    test_hh_mm_ss({24, 60, 0});
    test_hh_mm_ss({24, 60, 60});

    test_date_range({INT64_MIN, INT64_MIN});
    test_date_range({INT64_MIN, INT64_MIN + 1});
    test_date_range({INT64_MIN + 1, INT64_MIN});
    test_date_range({INT64_MIN + 1, INT64_MIN + 1});
    test_date_range({INT64_MIN, INT64_MIN / 2});
    test_date_range({INT64_MIN / 2, INT64_MIN});
    test_date_range({INT64_MIN / 2, INT64_MIN / 2});
    test_date_range({INT64_MIN, -1});
    test_date_range({-1, INT64_MIN});
    test_date_range({-1, -1});
    test_date_range({0, INT64_MIN});
    test_date_range({INT64_MIN, 0});
    test_date_range({0, 0});
    test_date_range({0, 1});
    test_date_range({1, 0});
    test_date_range({1, 1});
    test_date_range({1, INT64_MAX / 2});
    test_date_range({INT64_MAX / 2, 1});
    test_date_range({INT64_MAX / 2, INT64_MAX / 2});
    test_date_range({1, INT64_MAX - 1});
    test_date_range({INT64_MAX - 1, 1});
    test_date_range({INT64_MAX - 1, INT64_MAX - 1});
    test_date_range({1, INT64_MAX});
    test_date_range({INT64_MAX, 1});
    test_date_range({INT64_MAX, INT64_MAX});

    test_time_range({{0, 0, 0}, {0, 0, 0}});
    test_time_range({{1, 1, 1}, {0, 0, 0}});
    test_time_range({{0, 0, 0}, {1, 1, 1}});
    test_time_range({{1, 1, 1}, {1, 1, 1}});
    test_time_range({{0, 0, 0}, {12, 30, 30}});
    test_time_range({{12, 30, 30}, {0, 0, 0}});
    test_time_range({{12, 30, 30}, {12, 30, 30}});
    test_time_range({{0, 0, 0}, {23, 59, 59}});
    test_time_range({{23, 59, 59}, {0, 0, 0}});
    test_time_range({{23, 59, 59}, {23, 59, 59}});
    test_time_range({{0, 0, 0}, {24, 60, 60}});
    test_time_range({{24, 60, 60}, {0, 0, 0}});
    test_time_range({{24, 60, 60}, {24, 60, 60}});

    test_zone_offset(INT16_MIN);
    test_zone_offset(INT16_MIN + 1);
    test_zone_offset(INT16_MIN / 2);
    test_zone_offset(-1);
    test_zone_offset(0);
    test_zone_offset(1);
    test_zone_offset(INT16_MAX / 2);
    test_zone_offset(INT16_MAX - 1);
    test_zone_offset(INT16_MAX);

    test_zoned_time({0, 0});
    test_zoned_time({INT64_MIN, INT16_MIN});
    test_zoned_time({INT64_MIN, INT16_MIN + 1});
    test_zoned_time({INT64_MIN + 1, INT16_MIN});
    test_zoned_time({INT64_MIN + 1, INT16_MIN + 1});
    test_zoned_time({INT64_MIN, INT16_MIN / 2});
    test_zoned_time({INT64_MIN / 2, INT16_MIN});
    test_zoned_time({INT64_MIN / 2, INT16_MIN / 2});
    test_zoned_time({INT64_MIN, -1});
    test_zoned_time({-1, INT16_MIN});
    test_zoned_time({-1, -1});
    test_zoned_time({0, INT16_MIN});
    test_zoned_time({INT64_MIN, 0});
    test_zoned_time({0, 0});
    test_zoned_time({0, 1});
    test_zoned_time({1, 0});
    test_zoned_time({1, 1});
    test_zoned_time({1, INT16_MAX / 2});
    test_zoned_time({INT64_MAX / 2, 1});
    test_zoned_time({INT64_MAX / 2, INT16_MAX / 2});
    test_zoned_time({1, INT16_MAX - 1});
    test_zoned_time({INT64_MAX - 1, 1});
    test_zoned_time({INT64_MAX - 1, INT16_MAX - 1});
    test_zoned_time({1, INT16_MAX});
    test_zoned_time({INT64_MAX, 1});
    test_zoned_time({INT64_MAX, INT16_MAX});
}

TEST(eput_utils, other_conversion) {
    test_bool(true);
    test_bool(false);

    test_fixp32({INT32_MIN, INT32_MIN});
    test_fixp32({INT32_MIN, INT32_MIN + 1});
    test_fixp32({INT32_MIN + 1, INT32_MIN});
    test_fixp32({INT32_MIN + 1, INT32_MIN + 1});
    test_fixp32({INT32_MIN, INT32_MIN / 2});
    test_fixp32({INT32_MIN / 2, INT32_MIN});
    test_fixp32({INT32_MIN / 2, INT32_MIN / 2});
    test_fixp32({INT32_MIN, -1});
    test_fixp32({-1, INT32_MIN});
    test_fixp32({-1, -1});
    test_fixp32({INT32_MIN, 0});
    test_fixp32({0, INT32_MIN});
    test_fixp32({0, 0});
    test_fixp32({0, 1});
    test_fixp32({1, 0});
    test_fixp32({1, 1});
    test_fixp32({1, INT32_MAX / 2});
    test_fixp32({INT32_MAX / 2, 1});
    test_fixp32({INT32_MAX / 2, INT32_MAX / 2});
    test_fixp32({1, INT32_MAX - 1});
    test_fixp32({INT32_MAX - 1, 1});
    test_fixp32({INT32_MAX - 1, INT32_MAX - 1});
    test_fixp32({1, INT32_MAX});
    test_fixp32({INT32_MAX, 1});
    test_fixp32({INT32_MAX, INT32_MAX});

    test_fixp64({INT64_MIN, INT32_MIN});
    test_fixp64({INT64_MIN, INT32_MIN + 1});
    test_fixp64({INT64_MIN + 1, INT32_MIN});
    test_fixp64({INT64_MIN + 1, INT32_MIN + 1});
    test_fixp64({INT64_MIN, INT32_MIN / 2});
    test_fixp64({INT64_MIN / 2, INT32_MIN});
    test_fixp64({INT64_MIN / 2, INT32_MIN / 2});
    test_fixp64({INT64_MIN, -1});
    test_fixp64({-1, INT32_MIN});
    test_fixp64({-1, -1});
    test_fixp64({INT64_MIN, 0});
    test_fixp64({0, INT32_MIN});
    test_fixp64({0, 0});
    test_fixp64({0, 1});
    test_fixp64({1, 0});
    test_fixp64({1, 1});
    test_fixp64({1, INT32_MAX / 2});
    test_fixp64({INT64_MAX / 2, 1});
    test_fixp64({INT64_MAX / 2, INT32_MAX / 2});
    test_fixp64({1, INT32_MAX - 1});
    test_fixp64({INT64_MAX - 1, 1});
    test_fixp64({INT64_MAX - 1, INT32_MAX - 1});
    test_fixp64({1, INT32_MAX});
    test_fixp64({INT64_MAX, 1});
    test_fixp64({INT64_MAX, INT32_MAX});
}

TEST(eput_utils, get_ndef_tlv_offset) {
    FAIL() << "Not implemented";
}

TEST(eput_utils, get_record) {
    FAIL() << "Not implemented";
}

TEST(eput_utils, get_records) {
    FAIL() << "Not implemented";
}
