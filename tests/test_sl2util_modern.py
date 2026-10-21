"""
Comprehensive Automated Unit & Integration Tests for Modernized sl2util.
"""
import datetime
import socket
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import sl2util
import sl2util.configdatareader as cryptlib
import sl2util.dbhandler as db
import sl2util.utils as util
from sl2util import loader, logger, watchdog, watchdog_reader


# =====================================================================
# 1. Package Metadata & Import Tests
# =====================================================================
def test_package_metadata():
    assert sl2util.__version__ == "2.0.0"
    assert "Sergio Chavez Rangel" in sl2util.__author__


# =====================================================================
# 2. ConfigDataReader Tests
# =====================================================================
def test_key_derivation_and_encryption():
    password = b"SuperSecretSteelPassword123"
    key1 = cryptlib.get_key(password)
    key2 = cryptlib.get_key(password)
    assert key1 == key2  # Deterministic derivation
    assert len(key1) == 44  # Fernet key is 32 base64 urlsafe bytes

    cryptlib.set_key(key1)
    plain_text = "Heat=123456;Grade=A36;Furnace=EAF1"
    encrypted = cryptlib.getEncText(plain_text, log=False)
    assert encrypted != plain_text.encode("utf-8")

    decrypted = cryptlib.getDecText(encrypted, log=False).decode("utf-8")
    assert decrypted == plain_text


def test_xml_encode_decode_roundtrip(tmp_path: Path):
    dec_file = tmp_path / "Decrypted.xml"
    enc_file = tmp_path / "Encrypted.xml"

    # Create sample XML
    xml_content = """<?xml version="1.0"?>
<root>
    <Token value="122353"/>
    <FURNACE_ID value="EAF-01"/>
    <TARGET_TEMP value="1620"/>
</root>"""
    dec_file.write_text(xml_content, encoding="utf-8")

    cryptlib.setDecFilePath(dec_file, log=False)
    cryptlib.setEncFilePath(enc_file, log=False)

    key = cryptlib.get_key(b"TestPassword")
    cryptlib.set_key(key)

    # Encode XML
    cryptlib.encodeXML(log=False)
    assert enc_file.exists()
    assert "EAF-01" not in enc_file.read_text(encoding="utf-8")  # Values should be encrypted

    # Decode XML to memory
    decoded = cryptlib.decodeXML(save_file=False, log=False)
    assert decoded["Token"] == "122353"
    assert decoded["FURNACE_ID"] == "EAF-01"
    assert decoded["TARGET_TEMP"] == "1620"


def test_token_and_date_validation():
    # Today's date token should be valid
    today = datetime.date.today()
    future_date = today + datetime.timedelta(days=365)
    future_token = cryptlib.getTokenDate(future_date)
    assert cryptlib.isValidKey(future_token) is True

    # Far past date should be invalid
    past_date = datetime.date(2010, 1, 1)
    past_token = cryptlib.getTokenDate(past_date)
    assert cryptlib.isValidKey(past_token) is False

    # Expiration date string formatting
    exp_str = cryptlib.getExpireDate(future_token)
    assert exp_str.startswith(str(future_date.year))


# =====================================================================
# 3. Logger & Purger Tests
# =====================================================================
def test_logger_writelog_and_purger(tmp_path: Path):
    log_dir = tmp_path / "test_logs"
    logger.setPath(str(log_dir))
    logger.setFileName("automation_test")

    logger.writeLog("Testing Level 2 automation message #1")
    logger.writeLog("Testing Level 2 automation message #2")

    target_file = log_dir / "log" / "automation_test.txt"
    assert target_file.exists()

    content = target_file.read_text(encoding="utf-8")
    assert "Testing Level 2 automation message #1" in content
    assert "Testing Level 2 automation message #2" in content

    # Test purger size rotation
    logger.setKeepSize(10)  # Low threshold to trigger rotation
    logger.purger()
    rotated = list((log_dir / "log").glob("automation_test *.txt"))
    assert len(rotated) >= 1

    # Test purgeFiles
    logger.purgeFiles(days=0, path=log_dir / "log", file="automation_test *.txt")


def test_standard_logger_bridge():
    std_logger = logger.get_logger("sl2_test")
    assert std_logger.name == "sl2_test"
    std_logger.info("Informational message")


# =====================================================================
# 4. Utils: Steelmaking Text Decorator Tests
# =====================================================================
def test_text_decorator_steelmaking_tokens():
    test_date = datetime.date(2026, 10, 20)  # Tuesday
    template = "Heat: %Heat | Tmt: %Tmt | Shift: %Shift | InSeq: %InSeq | Date: %yyyy-%mm-%dd | Day: %day"
    formatted = util.text_decorator(
        text=template,
        date=test_date,
        shift=21,  # 21 -> Shift 'A'
        heat=994512,
        tmt=1,
        sequence=5,
        in_seq=3,  # Should format as '03'
    )

    assert "Heat: 994512" in formatted
    assert "Tmt: 1" in formatted
    assert "Shift: A" in formatted
    assert "InSeq: 03" in formatted
    assert "Date: 2026-10-20" in formatted
    assert "Day: Tuesday" in formatted


def test_text_decorator_shift_mapping():
    d = datetime.date(2026, 5, 1)
    assert util.text_decorator("%Shift", d, 21, 0, 0, 0, 0) == "A"
    assert util.text_decorator("%Shift", d, 22, 0, 0, 0, 0) == "B"
    assert util.text_decorator("%Shift", d, 23, 0, 0, 0, 0) == "C"


# =====================================================================
# 5. Utils: Cross-Platform Zip and File Management Tests
# =====================================================================
def test_cross_platform_zipper(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    sample_file = src_dir / "report.txt"
    sample_file.write_text("Daily Steelmaking Report - Furnace #2", encoding="utf-8")

    zip_dir = tmp_path / "archives"
    zip_dir.mkdir()

    success = util.zipper("report.txt", src_dir, zip_dir)
    assert success is True

    zip_file = zip_dir / "report.zip"
    assert zip_file.exists()

    # Verify zip content
    import zipfile
    with zipfile.ZipFile(zip_file, "r") as zf:
        assert "report.txt" in zf.namelist()
        extracted_content = zf.read("report.txt").decode("utf-8")
        assert "Daily Steelmaking Report" in extracted_content


def test_file_operations(tmp_path: Path):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    fname = "test_data.txt"

    # Append
    util.file_append("Line 1", work_dir, fname)
    util.file_append("Line 2", work_dir, fname)
    assert util.files_exists("test_data.txt", work_dir) is True

    # Copy
    dest_dir = tmp_path / "dest"
    util.copy_file(fname, work_dir, dest_dir)
    assert util.files_exists(fname, dest_dir) is True

    # Empty
    util.file_empty(work_dir, fname)
    assert (work_dir / fname).read_text() == ""

    # Delete
    util.delete_file(fname, work_dir)
    assert util.files_exists(fname, work_dir) is False


# =====================================================================
# 6. Watchdog Server & Reader Heartbeat Integration Test
# =====================================================================
def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def test_watchdog_server_and_reader_roundtrip():
    free_port = _find_free_port()
    server = watchdog.WatchdogServer("test_l2_service", free_port)
    server.start("127.0.0.1")

    try:
        # Give thread a moment to bind and listen
        time.sleep(0.1)

        # Call service using watchdog_reader
        response = watchdog_reader.call_service("127.0.0.1", free_port, timeout=2.0)
        assert response == "RUN"
    finally:
        server.stop()


# =====================================================================
# 7. Database Handler Unit Tests (Mocked DB connections)
# =====================================================================
def test_rows_to_dict_list():
    mock_cursor = MagicMock()
    mock_cursor.description = [("HEAT_ID",), ("GRADE",), ("WEIGHT_TONS",)]
    mock_cursor.fetchall.return_value = [
        (1001, "304L", 125.5),
        (1002, "316L", 130.0),
    ]

    result = db.rows_to_dict_list(mock_cursor)
    assert len(result) == 2
    assert result[0] == {"HEAT_ID": 1001, "GRADE": "304L", "WEIGHT_TONS": 125.5}
    assert result[1] == {"HEAT_ID": 1002, "GRADE": "316L", "WEIGHT_TONS": 130.0}


def test_dbora_with_mock():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.description = [("SYSDATE",)]
    mock_cursor.fetchall.return_value = [("2026-10-20 21:00:00",)]

    with patch("sl2util.dbhandler._ORA_MODULE") as mock_ora:
        mock_ora.connect.return_value = mock_conn
        ora = db.DbOra("fake_user/fake_pwd@fake_host/fake_db")
        row = ora.getrow("SELECT sysdate FROM dual")
        assert row == {"SYSDATE": "2026-10-20 21:00:00"}
        ora.close()
        mock_conn.close.assert_called_once()


# =====================================================================
# 8. Loader & NOT_KEY Safety Tests
# =====================================================================
def test_loader_safe_state():
    assert loader.NOT_KEY() is True
    assert isinstance(loader.fixed_config, dict)
    assert isinstance(loader.open_config, dict)
