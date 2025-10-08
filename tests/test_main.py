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
def mock_ultrasonic_sensor() -> Generator[MagicMock, None, None]:
    """Fixture to mock UltrasonicSensor class."""
    with patch("rpi_electronics_playground.main.UltrasonicSensor") as mock:
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
        mock_ultrasonic_sensor: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function initialization."""
        # Mock sensor to return a distance then trigger exit
        mock_sensor_instance = mock_ultrasonic_sensor.return_value
        mock_sensor_instance.get_distance.side_effect = [25.0, KeyboardInterrupt()]

        with caplog.at_level(logging.INFO):
            run()

        # Verify LCD initialization
        mock_lcd.assert_called_once_with(address=0x27, backlight=True)

        # Verify ultrasonic sensor initialization
        mock_ultrasonic_sensor.assert_called_once_with(
            trig_pin=5, echo_pin=6, sample_count=3, filter_size=5, outlier_threshold=5.0
        )

        # Verify initial LCD messages
        lcd_instance = mock_lcd.return_value
        lcd_write_calls = lcd_instance.write.call_args_list

        # Check startup messages
        assert any("[STARTUP]" in str(call) for call in lcd_write_calls)
        assert any("Initializing..." in str(call) for call in lcd_write_calls)
        assert any("[READY]" in str(call) for call in lcd_write_calls)
        assert any("System Ready!" in str(call) for call in lcd_write_calls)

        # Verify logging messages
        assert "Initializing Raspberry Pi Electronics Playground..." in caplog.text
        assert "System initialized successfully!" in caplog.text

        # Verify cleanup
        lcd_instance.cleanup.assert_called_once()
        mock_sensor_instance.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_distance_measurement_loop(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_ultrasonic_sensor: MagicMock,
        mock_sleep: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function distance measurement loop."""
        # Mock sensor to return some distances then trigger exit
        mock_sensor_instance = mock_ultrasonic_sensor.return_value
        mock_sensor_instance.get_distance.side_effect = [25.3, 24.8, 26.1, KeyboardInterrupt()]

        with caplog.at_level(logging.INFO):
            run()

        # Verify distance measurements were called
        assert mock_sensor_instance.get_distance.call_count >= 3

        # Verify distance logging
        assert "Distance: 25.30 cm" in caplog.text
        assert "Distance: 24.80 cm" in caplog.text

        # Verify LCD distance displays
        lcd_instance = mock_lcd.return_value
        lcd_write_calls = lcd_instance.write.call_args_list

        # Should have [MEASURE] headers and distance readings
        assert any("[MEASURE]" in str(call) for call in lcd_write_calls)
        assert any("Dist: 25.3 cm" in str(call) for call in lcd_write_calls)
        assert any("Dist: 24.8 cm" in str(call) for call in lcd_write_calls)

        # Verify sleep was called between measurements
        mock_sleep.assert_called()

    def test_run_distance_measurement_error(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_ultrasonic_sensor: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with distance measurement errors."""
        # Mock sensor to return error readings then trigger exit
        mock_sensor_instance = mock_ultrasonic_sensor.return_value
        mock_sensor_instance.get_distance.side_effect = [-1.0, -1.0, KeyboardInterrupt()]

        with caplog.at_level(logging.INFO):
            run()

        # Verify error distance logging
        assert "Distance: -1.00 cm" in caplog.text

        # Verify LCD error display
        lcd_instance = mock_lcd.return_value
        lcd_write_calls = lcd_instance.write.call_args_list

        # Should show reading error on LCD
        assert any("Reading Error" in str(call) for call in lcd_write_calls)

    def test_run_keyboard_interrupt(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_ultrasonic_sensor: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function with KeyboardInterrupt during main loop."""
        # Mock sensor to trigger KeyboardInterrupt immediately
        mock_sensor_instance = mock_ultrasonic_sensor.return_value
        mock_sensor_instance.get_distance.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.INFO):
            run()

        # Verify shutdown messages
        lcd_instance = mock_lcd.return_value
        lcd_write_calls = lcd_instance.write.call_args_list

        # Should show shutdown messages
        assert any("[SHUTDOWN]" in str(call) for call in lcd_write_calls)
        assert any("Goodbye!" in str(call) for call in lcd_write_calls)

        assert "Shutting down system..." in caplog.text
        assert "Cleaning up resources..." in caplog.text
        assert "System shutdown complete!" in caplog.text

        # Verify cleanup
        lcd_instance.set_backlight.assert_called_with(False)
        lcd_instance.cleanup.assert_called_once()
        mock_sensor_instance.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_unexpected_exception(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_ultrasonic_sensor: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function handling unexpected exceptions."""
        # Mock sensor to raise an unexpected exception
        mock_sensor_instance = mock_ultrasonic_sensor.return_value
        mock_sensor_instance.get_distance.side_effect = RuntimeError("Sensor failure!")

        with caplog.at_level(logging.INFO):
            run()

        # Verify error handling
        lcd_instance = mock_lcd.return_value
        lcd_write_calls = lcd_instance.write.call_args_list

        # Should show error messages
        assert any("[ERROR]" in str(call) for call in lcd_write_calls)
        assert any("Check logs!" in str(call) for call in lcd_write_calls)

        assert "Unexpected error occurred!" in caplog.text
        assert "Cleaning up resources..." in caplog.text
        assert "System shutdown complete!" in caplog.text

        # Verify cleanup
        lcd_instance.set_backlight.assert_called_with(False)
        lcd_instance.cleanup.assert_called_once()
        mock_sensor_instance.cleanup.assert_called_once()
        mock_gpio.cleanup.assert_called_once()

    def test_run_lcd_initialization_error(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_ultrasonic_sensor: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when LCD initialization fails."""
        # Mock LCD to raise exception during initialization
        mock_lcd.side_effect = RuntimeError("LCD initialization failed!")

        with caplog.at_level(logging.INFO):
            run()

        # Should attempt LCD initialization
        mock_lcd.assert_called_once_with(address=0x27, backlight=True)

        # Should log the error
        assert "Unexpected error occurred!" in caplog.text

        # Should still cleanup GPIO
        mock_gpio.cleanup.assert_called_once()

    def test_run_sensor_initialization_error(
        self,
        mock_gpio: MagicMock,
        mock_lcd: MagicMock,
        mock_ultrasonic_sensor: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test run function when ultrasonic sensor initialization fails."""
        # Mock sensor to raise exception during initialization
        mock_ultrasonic_sensor.side_effect = RuntimeError("Sensor initialization failed!")

        with caplog.at_level(logging.INFO):
            run()

        # Should attempt sensor initialization
        mock_ultrasonic_sensor.assert_called_once_with(
            trig_pin=5, echo_pin=6, sample_count=3, filter_size=5, outlier_threshold=5.0
        )

        # Should log the error
        assert "Unexpected error occurred!" in caplog.text

        # Should still cleanup GPIO and LCD
        mock_gpio.cleanup.assert_called_once()
        # LCD should be cleaned up if it was created before sensor failed
        if mock_lcd.return_value.cleanup.called:
            mock_lcd.return_value.cleanup.assert_called_once()
