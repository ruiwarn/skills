#!/usr/bin/env python3
"""
TDD Tests for DLT698.45 Protocol (proto_698.py)
Based on DL/T698.45 official specification.

Key references:
- Section 6.2: Frame format (68 LL C SA CA HCS APDU FCS 16)
- Appendix D: CRC16/FCS-16 algorithm (polynomial 0x8408, init 0xFFFF, complement)
- Section 7.2: A-XDR data type tags
- Appendix H: APDU encoding examples
"""
import sys
import os
import struct
import unittest

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


class TestCRC16FCS(unittest.TestCase):
    """Test CRC16/FCS-16 per DL/T698.45 Appendix D.
    
    The polynomial is x^0+x^5+x^12+x^16, reflected = 0x8408.
    Initial value = 0xFFFF, final XOR = 0xFFFF (complement).
    """

    def test_known_vector_fcs16(self):
        """FCS-16 of ASCII '123456789' should be 0x906E (per ITU-T X.25 / RFC1662)."""
        from proto_698 import calc_fcs16
        data = b'123456789'
        result = calc_fcs16(data)
        self.assertEqual(result, 0x906E, f"FCS-16('123456789') should be 0x906E, got 0x{result:04X}")

    def test_empty_data(self):
        from proto_698 import calc_fcs16
        result = calc_fcs16(b'')
        self.assertEqual(result, 0x0000)

    def test_single_byte(self):
        from proto_698 import calc_fcs16
        result = calc_fcs16(b'\x00')
        self.assertIsInstance(result, int)
        self.assertTrue(0 <= result <= 0xFFFF)


class TestAddrParsing(unittest.TestCase):
    """Test server/client address parsing per Section 6.2.4."""

    def test_parse_server_addr_single(self):
        from proto_698 import parse_server_addr
        sa = parse_server_addr("123456789012", addr_type=0, logic_addr=0)
        self.assertEqual(sa[0], 0x05)
        self.assertEqual(sa[1:], bytes.fromhex("123456789012"))

    def test_parse_server_addr_wildcard(self):
        from proto_698 import parse_server_addr
        sa = parse_server_addr("AAAAAAAAAAAA", addr_type=1, logic_addr=0)
        self.assertEqual(sa[0], 0x45)
        self.assertEqual(sa[1:], bytes.fromhex("AAAAAAAAAAAA"))

    def test_parse_server_addr_broadcast(self):
        from proto_698 import parse_server_addr
        sa = parse_server_addr("AAAAAAAAAAAA", addr_type=3, logic_addr=0)
        self.assertEqual(sa[0], 0xC5)

    def test_parse_client_addr(self):
        from proto_698 import parse_client_addr
        ca = parse_client_addr("00")
        self.assertEqual(ca, b'\x00')
        ca = parse_client_addr("10")
        self.assertEqual(ca, b'\x10')


class TestControlByte(unittest.TestCase):
    """Test control byte construction per Section 6.2.3."""

    def test_downlink_request(self):
        from proto_698 import build_ctrl_byte
        ctrl = build_ctrl_byte(is_downlink=True, is_start_station=True,
                               slice_flag=False, sc_flag=False, func_code=3)
        self.assertEqual(ctrl, 0x43)

    def test_uplink_response(self):
        from proto_698 import build_ctrl_byte
        ctrl = build_ctrl_byte(is_downlink=False, is_start_station=False,
                               slice_flag=False, sc_flag=False, func_code=3)
        self.assertEqual(ctrl, 0x83)

    def test_link_management(self):
        from proto_698 import build_ctrl_byte
        ctrl = build_ctrl_byte(is_downlink=False, is_start_station=False,
                               slice_flag=False, sc_flag=False, func_code=1)
        self.assertEqual(ctrl, 0x81)


class TestFrameBuilding(unittest.TestCase):
    """Test complete frame building.
    
    Correct frame format: 68 LL C SA CA HCS APDU FCS 16
    """

    def test_frame_starts_with_68(self):
        from proto_698 import encode_request
        frame = encode_request("AAAAAAAAAAAA", "00", "read", "40010200")
        self.assertEqual(frame[0], 0x68)

    def test_frame_ends_with_16(self):
        from proto_698 import encode_request
        frame = encode_request("AAAAAAAAAAAA", "00", "read", "40010200")
        self.assertEqual(frame[-1], 0x16)

    def test_frame_has_no_second_68(self):
        from proto_698 import encode_request
        frame = encode_request("AAAAAAAAAAAA", "00", "read", "40010200")
        self.assertEqual(frame[3], 0x43,
                         f"Byte at pos3 should be control byte 0x43, got 0x{frame[3]:02X}")

    def test_length_field_correct(self):
        from proto_698 import encode_request
        frame = encode_request("AAAAAAAAAAAA", "00", "read", "40010200")
        len_field = struct.unpack("<H", frame[1:3])[0] & 0x3FFF
        self.assertEqual(len_field, len(frame) - 2,
                         f"L should be {len(frame) - 2}, got {len_field}")

    def test_hcs_verification(self):
        from proto_698 import encode_request, calc_fcs16
        frame = encode_request("AAAAAAAAAAAA", "00", "read", "40010200")
        sa_len = 7
        hcs_pos = 1 + 2 + 1 + sa_len + 1
        hcs_recv = struct.unpack("<H", frame[hcs_pos:hcs_pos+2])[0]
        hcs_data = frame[1:hcs_pos]
        hcs_calc = calc_fcs16(hcs_data)
        self.assertEqual(hcs_calc, hcs_recv,
                         f"HCS mismatch: calc=0x{hcs_calc:04X}, recv=0x{hcs_recv:04X}")

    def test_fcs_verification(self):
        from proto_698 import encode_request, calc_fcs16
        frame = encode_request("AAAAAAAAAAAA", "00", "read", "40010200")
        fcs_recv = struct.unpack("<H", frame[-3:-1])[0]
        fcs_data = frame[1:-3]
        fcs_calc = calc_fcs16(fcs_data)
        self.assertEqual(fcs_calc, fcs_recv,
                         f"FCS mismatch: calc=0x{fcs_calc:04X}, recv=0x{fcs_recv:04X}")

    def test_get_request_apdu_format(self):
        from proto_698 import encode_request
        frame = encode_request("AAAAAAAAAAAA", "00", "read", "40010200")
        sa_len = 7
        apdu_start = 1 + 2 + 1 + sa_len + 1 + 2
        apdu = frame[apdu_start:-3]
        
        self.assertEqual(apdu[0], 0x05, "First APDU byte should be 0x05 (GET-Request)")
        self.assertEqual(apdu[1], 0x01, "Second byte should be 0x01 (GetRequestNormal)")
        self.assertEqual(apdu[3:7], bytes.fromhex("40010200"), "OAD should be 40010200")
        self.assertEqual(apdu[-1], 0x00, "Last byte should be 0x00 (no TimeTag)")

    def test_set_request_apdu_format(self):
        from proto_698 import encode_request
        frame = encode_request("AAAAAAAAAAAA", "00", "set", "40010200", value="uint8:100")
        sa_len = 7
        apdu_start = 1 + 2 + 1 + sa_len + 1 + 2
        apdu = frame[apdu_start:-3]
        
        self.assertEqual(apdu[0], 0x06, "First APDU byte should be 0x06 (SET-Request)")
        self.assertEqual(apdu[1], 0x01, "Second byte should be 0x01 (SetRequestNormal)")
        self.assertEqual(apdu[-1], 0x00, "Last byte should be 0x00 (no TimeTag)")


class TestFrameParsing(unittest.TestCase):
    """Test response frame parsing."""

    def _build_test_response_frame(self):
        from proto_698 import calc_fcs16
        
        sa = bytes([0x45]) + bytes.fromhex("AAAAAAAAAAAA")
        ca = bytes([0x00])
        ctrl = 0x83

        apdu = bytes([0x85, 0x01, 0x01])
        apdu += bytes.fromhex("40010200")
        apdu += bytes([0x01])
        apdu += bytes([0x09, 0x06])
        apdu += bytes.fromhex("123456789012")
        apdu += bytes([0x00])
        apdu += bytes([0x00])
        
        l_value = 2 + 1 + len(sa) + len(ca) + 2 + len(apdu) + 2
        len_bytes = struct.pack("<H", l_value & 0x3FFF)
        
        hcs_data = len_bytes + bytes([ctrl]) + sa + ca
        hcs = calc_fcs16(hcs_data)
        hcs_bytes = struct.pack("<H", hcs)
        
        fcs_data = len_bytes + bytes([ctrl]) + sa + ca + hcs_bytes + apdu
        fcs = calc_fcs16(fcs_data)
        fcs_bytes = struct.pack("<H", fcs)
        
        frame = bytes([0x68]) + len_bytes + bytes([ctrl]) + sa + ca + hcs_bytes + apdu + fcs_bytes + bytes([0x16])
        return frame

    def test_parse_valid_response(self):
        from proto_698 import parse_response
        frame = self._build_test_response_frame()
        rsp = parse_response(frame)
        
        self.assertTrue(rsp.frame_complete, f"Frame should be complete: {rsp.error}")
        self.assertTrue(rsp.hcs_ok, "HCS should verify")
        self.assertTrue(rsp.fcs_ok, "FCS should verify")
        self.assertTrue(rsp.frame_valid, "Frame should be valid")

    def test_parse_service_type(self):
        from proto_698 import parse_response
        frame = self._build_test_response_frame()
        rsp = parse_response(frame)
        
        self.assertEqual(rsp.service_type, 0x85)

    def test_parse_oad(self):
        from proto_698 import parse_response
        frame = self._build_test_response_frame()
        rsp = parse_response(frame)
        
        self.assertEqual(rsp.oad, "40010200")

    def test_parse_data(self):
        from proto_698 import parse_response
        frame = self._build_test_response_frame()
        rsp = parse_response(frame)
        
        self.assertTrue(len(rsp.data) > 0, "Should have data")

    def test_find_complete_frame(self):
        from proto_698 import find_complete_frame
        frame = self._build_test_response_frame()
        
        stream = b'\xFE\xFE\xFE\xFE' + frame + b'\x00\x00\x00'
        found = find_complete_frame(stream)
        self.assertIsNotNone(found, "Should find frame in stream")
        self.assertEqual(found, frame, "Found frame should match original")

    def test_find_frame_in_noise(self):
        from proto_698 import find_complete_frame
        frame = self._build_test_response_frame()
        
        stream = b'\x00\x01\x02\x03\x04' + frame
        found = find_complete_frame(stream)
        self.assertIsNotNone(found)
        self.assertEqual(found, frame)


class TestRoundTrip(unittest.TestCase):
    """Test that build → parse round trip works."""

    def test_get_request_roundtrip(self):
        from proto_698 import encode_request, calc_fcs16
        
        request = encode_request("AAAAAAAAAAAA", "00", "read", "40010200")
        
        self.assertEqual(request[0], 0x68)
        self.assertEqual(request[-1], 0x16)
        
        len_field = struct.unpack("<H", request[1:3])[0] & 0x3FFF
        self.assertEqual(len_field, len(request) - 2)


class TestValueCodec698(unittest.TestCase):
    """Test A-XDR value encoding per Section 7.2 data type tags."""

    def test_bool_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("bool:true")
        self.assertEqual(result[0], 3)
        self.assertEqual(result[1], 1)

    def test_bool_false(self):
        from value_codec import encode_698_value
        result = encode_698_value("bool:false")
        self.assertEqual(result[0], 3)
        self.assertEqual(result[1], 0)

    def test_int8_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("int8:42")
        self.assertEqual(result[0], 15)

    def test_int16_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("int16:1000")
        self.assertEqual(result[0], 16)

    def test_int32_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("int32:100000")
        self.assertEqual(result[0], 5)

    def test_uint8_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("uint8:200")
        self.assertEqual(result[0], 17)

    def test_uint16_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("uint16:50000")
        self.assertEqual(result[0], 18)

    def test_uint32_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("uint32:100000")
        self.assertEqual(result[0], 6)

    def test_enum_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("enum:5")
        self.assertEqual(result[0], 22)

    def test_octet_string_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("octet:112233")
        self.assertEqual(result[0], 9)

    def test_visible_string_tag(self):
        from value_codec import encode_698_value
        result = encode_698_value("string:abc")
        self.assertEqual(result[0], 10)

    def test_int8_encoding(self):
        from value_codec import encode_698_value
        result = encode_698_value("int8:-1")
        self.assertEqual(result, bytes([15, 0xFF]))

    def test_int16_encoding(self):
        from value_codec import encode_698_value
        result = encode_698_value("int16:256")
        self.assertEqual(result, bytes([16, 0x01, 0x00]))

    def test_uint8_encoding(self):
        from value_codec import encode_698_value
        result = encode_698_value("uint8:200")
        self.assertEqual(result, bytes([17, 200]))

    def test_uint16_encoding(self):
        from value_codec import encode_698_value
        result = encode_698_value("uint16:1000")
        self.assertEqual(result, bytes([18, 0x03, 0xE8]))


class TestAppendixHExamples(unittest.TestCase):
    """Verify against concrete examples from Appendix H."""

    def test_get_request_apdu_read_comm_addr(self):
        from proto_698 import build_apdu_get_normal
        apdu = build_apdu_get_normal("40010200", piid=0x01)
        expected = bytes([0x05, 0x01, 0x01]) + bytes.fromhex("40010200") + bytes([0x00])
        self.assertEqual(apdu, expected,
                         f"Expected {expected.hex()}, got {apdu.hex()}")

    def test_get_response_parse(self):
        from proto_698 import parse_apdu
        apdu = bytes([0x85, 0x01, 0x01]) + bytes.fromhex("40010200")
        apdu += bytes([0x01, 0x09, 0x06]) + bytes.fromhex("123456789012")
        apdu += bytes([0x00, 0x00])
        
        result = parse_apdu(apdu)
        self.assertEqual(result["service_type"], 0x85)
        self.assertEqual(result["service_response"], 0x01)
        self.assertEqual(result["oad"], "40010200")


if __name__ == '__main__':
    unittest.main(verbosity=2)
