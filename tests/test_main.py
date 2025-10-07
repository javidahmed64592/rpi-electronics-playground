"""Unit tests for the rpi_electronics_playground.main module."""

import logging
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rpi_electronics_playground.main import run


@pytest.fixture
def mock_gpio() -> Generator[MagicMock, None, None]:
    """Fixture to mock GPIO module."""
    with patch("rpi_electronics_playground.main.GPIO") as mock:
        yield mock


@pytest.fixture
def mock_lcd() -> Generator[MagicMock, None, None]:
    """Fixture to mock LCD1602 class."""
    with patch("rpi_electronics_playground.main.LCD1602") as mock:
        yield mock


@pytest.fixture
def mock_sleep() -> Generator[MagicMock, None, None]:
    """Fixture to mock time.sleep."""
    with patch("rpi_electronics_playground.main.time.sleep") as mock:
        yield mock


class TestRun:
    """Unit tests for the run function."""

    def test_run_initialization(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function initialization."""
        # Make the loop exit immediately with KeyboardInterrupt
        mock_lcd.return_value.write.side_effect = [None, None, None, None, KeyboardInterrupt()]

        with caplog.at_level(logging.INFO):
            run()

        # Verify LCD initialization
        mock_lcd.assert_called_once_with(address=0x27, backlight=True)

        # Verify initial LCD writes
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        min_expected_calls = 4
        assert len(lcd_write_calls) >= min_expected_calls  # Initial setup calls

        # Check initialization messages
        assert lcd_write_calls[0][0] == (0, 0, "Electronics Playground")
        assert lcd_write_calls[1][0] == (0, 1, "Initializing...")
        assert lcd_write_calls[2][0] == (0, 0, "Electronics Playground")
        assert lcd_write_calls[3][0] == (0, 1, "Ready!")

        # Verify logging messages
        assert "Initializing Raspberry Pi Electronics Playground..." in caplog.text
        assert "System initialized successfully!" in caplog.text

        # Verify cleanup
        mock_lcd.return_value.clear.assert_called()
        mock_lcd.return_value.set_backlight.assert_called_with(backlight=False)
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_counter_loop(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function counter loop with a few iterations."""
        # Let it run for a couple iterations then interrupt
        loop_count = 0

        def side_effect(*args: object) -> None:
            nonlocal loop_count
            loop_count += 1
            max_calls = 6  # Initial setup (4) + 2 loop iterations
            if loop_count > max_calls:
                raise KeyboardInterrupt()

        mock_lcd.return_value.write.side_effect = side_effect

        with caplog.at_level(logging.INFO):
            run()

        # Verify counter logging
        assert "Timestep: 0" in caplog.text
        assert "Timestep: 1" in caplog.text

        # Verify sleep was called
        mock_sleep.assert_called()

        # Verify LCD displays timesteps
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        # Should have timestep displays
        timestep_calls = [call for call in lcd_write_calls if "Timestep:" in str(call)]
        min_expected_timesteps = 2
        assert len(timestep_calls) >= min_expected_timesteps

    def test_run_keyboard_interrupt(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with KeyboardInterrupt during main loop."""
        # Let initialization complete, then interrupt during first loop iteration
        call_count = 0

        def side_effect(*args: object) -> None:
            nonlocal call_count
            call_count += 1
            max_setup_calls = 5  # After initial setup
            if call_count > max_setup_calls:
                raise KeyboardInterrupt()

        mock_lcd.return_value.write.side_effect = side_effect

        with caplog.at_level(logging.INFO):
            run()

        # Verify shutdown messages
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        shutdown_calls = [call for call in lcd_write_calls if "Shutting Down" in str(call) or "Goodbye!" in str(call)]
        min_expected_shutdown_calls = 2
        assert len(shutdown_calls) >= min_expected_shutdown_calls

        assert "Shutting down system..." in caplog.text
        assert "Cleaning up resources..." in caplog.text
        assert "System shutdown complete!" in caplog.text

        # Verify cleanup
        mock_lcd.return_value.set_backlight.assert_called_with(backlight=False)
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_unexpected_exception(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function handling unexpected exceptions."""
        # Let initialization complete, then raise an unexpected exception
        call_count = 0

        def side_effect(*args: object) -> None:
            nonlocal call_count
            call_count += 1
            max_setup_calls = 5  # After initial setup
            if call_count > max_setup_calls:
                error_msg = "Unexpected error!"
                raise RuntimeError(error_msg)

        mock_lcd.return_value.write.side_effect = side_effect

        with caplog.at_level(logging.INFO):
            run()

        # Verify error handling
        lcd_write_calls = mock_lcd.return_value.write.call_args_list
        error_calls = [call for call in lcd_write_calls if "System Error" in str(call) or "Check logs!" in str(call)]
        min_expected_error_calls = 2
        assert len(error_calls) >= min_expected_error_calls

        assert "Unexpected error occurred!" in caplog.text
        assert "Cleaning up resources..." in caplog.text
        assert "System shutdown complete!" in caplog.text

        # Verify cleanup
        mock_lcd.return_value.set_backlight.assert_called_with(backlight=False)
        mock_lcd.return_value.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_lcd_initialization_error(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when LCD initialization fails."""
        initialization_error = "LCD initialization failed!"
        mock_lcd.side_effect = RuntimeError(initialization_error)

        with caplog.at_level(logging.INFO):
            run()

        # Should still attempt to initialize
        mock_lcd.assert_called_once_with(address=0x27, backlight=True)

        # Should log the error
        assert "Unexpected error occurred!" in caplog.text

        # Should still cleanup GPIO
        mock_gpio.cleanup.assert_called_once()
