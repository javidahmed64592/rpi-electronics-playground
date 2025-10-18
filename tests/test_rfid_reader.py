"""Unit tests for the rpi_electronics_playground.rfid_reader module."""

import logging
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rpi_electronics_playground.rfid_reader import RFIDReader


@pytest.fixture
def mock_simple_mfrc522() -> Generator[MagicMock, None, None]:
    """Fixture to mock SimpleMFRC522."""
    with patch("rpi_electronics_playground.rfid_reader.SimpleMFRC522") as mock:
        mock_reader = MagicMock()
        mock.return_value = mock_reader
        yield mock_reader


@pytest.fixture
def mock_gpio() -> Generator[MagicMock, None, None]:
    """Fixture to mock GPIO module."""
    with patch("rpi_electronics_playground.rfid_reader.GPIO") as mock:
        mock.getmode.return_value = None
        yield mock


class TestRFIDReader:
    """Unit tests for the RFIDReader class."""

    def test_init(self, mock_simple_mfrc522: MagicMock, mock_gpio: MagicMock) -> None:
        """Test RFIDReader initialization."""
        rfid_reader = RFIDReader()

        assert rfid_reader.component_name == "RFIDReader"
        assert rfid_reader.is_initialized is True
        mock_simple_mfrc522.__init__.assert_called_once()

    def test_context_manager(self, mock_simple_mfrc522: MagicMock, mock_gpio: MagicMock) -> None:
        """Test RFIDReader works as context manager."""
        with RFIDReader() as rfid_reader:
            assert rfid_reader.component_name == "RFIDReader"
            assert rfid_reader.is_initialized is True

        # GPIO cleanup should be called
        mock_gpio.cleanup.assert_called()

    @pytest.mark.parametrize(
        ("card_id", "text"),
        [
            (987654321, "password123"),
            (555555555, "secret_key"),
            (111111111, ""),
            (999999999, "very_long_password_text_that_might_be_stored_on_card"),
        ],
    )
    def test_read_card(
        self, mock_simple_mfrc522: MagicMock, card_id: int, text: str, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test reading cards with various data combinations."""
        mock_simple_mfrc522.read.return_value = (card_id, text)

        rfid_reader = RFIDReader()
        result = rfid_reader.read_card()

        assert result == (card_id, text)
        mock_simple_mfrc522.read.assert_called_once()

    def test_read_card_exception(self, mock_simple_mfrc522: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test card reading when an exception occurs."""
        mock_simple_mfrc522.read.side_effect = Exception("RFID read error")

        rfid_reader = RFIDReader()

        with caplog.at_level(logging.ERROR):
            result = rfid_reader.read_card()

        assert result is None
        assert "Error reading card!" in caplog.text
        mock_simple_mfrc522.read.assert_called_once()

    @pytest.mark.parametrize(
        "test_text",
        [
            "simple_password",
            "password_with_123_numbers",
            "",
            "special_chars_!@#$%^&*()",
            "a" * 100,
        ],
    )
    def test_write_card(self, mock_simple_mfrc522: MagicMock, test_text: str) -> None:
        """Test writing various types of text to cards."""
        rfid_reader = RFIDReader()

        result = rfid_reader.write_card(test_text)

        mock_simple_mfrc522.write.assert_called_once_with(test_text)
        assert result is True

    def test_write_card_exception(self, mock_simple_mfrc522: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test card writing when an exception occurs."""
        test_text = "test_password"
        mock_simple_mfrc522.write.side_effect = Exception("RFID write error")

        rfid_reader = RFIDReader()

        with caplog.at_level(logging.ERROR):
            result = rfid_reader.write_card(test_text)

        assert result is False
        assert "Error writing to card!" in caplog.text
        mock_simple_mfrc522.write.assert_called_once_with(test_text)
