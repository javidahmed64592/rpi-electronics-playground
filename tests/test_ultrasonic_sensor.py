"""Unit tests for the rpi_electronics_playground.ultrasonic_sensor module."""

import logging
from collections import deque
from collections.abc import Generator
from unittest.mock import MagicMock, call, patch

import pytest

from rpi_electronics_playground.ultrasonic_sensor import UltrasonicSensor


@pytest.fixture
def mock_gpio() -> Generator[MagicMock, None, None]:
    """Fixture to mock GPIO module."""
    with patch("rpi_electronics_playground.ultrasonic_sensor.GPIO") as mock:
        yield mock


@pytest.fixture
def mock_time() -> Generator[MagicMock, None, None]:
    """Fixture to mock time module."""
    with patch("rpi_electronics_playground.ultrasonic_sensor.time") as mock:
        yield mock


class TestUltrasonicSensor:
    """Unit tests for UltrasonicSensor core functionality."""

    def test_initialization(self, mock_gpio: MagicMock) -> None:
        """Test sensor initialization with default and custom parameters."""
        # Test default parameters
        sensor = UltrasonicSensor()

        assert sensor.trig_pin == 5
        assert sensor.echo_pin == 6
        assert sensor.sample_count == 5
        assert sensor.filter_size == 10
        assert isinstance(sensor.readings_buffer, deque)
        assert sensor.last_stable_reading is None

        # Verify GPIO setup
        mock_gpio.setmode.assert_called_with(mock_gpio.BCM)
        mock_gpio.setup.assert_any_call(5, mock_gpio.OUT)
        mock_gpio.setup.assert_any_call(6, mock_gpio.IN)

    def test_single_distance_measurement(self, mock_gpio: MagicMock, mock_time: MagicMock) -> None:
        """Test single distance measurement with successful reading."""
        # Mock GPIO input sequence for echo response
        mock_gpio.input.side_effect = [
            mock_gpio.LOW,  # First check in wait-for-HIGH loop
            mock_gpio.HIGH,  # Echo goes HIGH (exits first loop)
            mock_gpio.HIGH,  # First check in wait-for-LOW loop
            mock_gpio.LOW,  # Echo goes LOW (exits second loop)
        ]

        # Mock time.time() calls:
        # 1. Initial timeout_start time
        # 2. pulse_start time (when echo goes HIGH)
        # 3. Initial timeout_end time
        # 4. pulse_end time (when echo goes LOW)
        # Pulse duration: 1.0001 - 1.0 = 0.0001 seconds = 1.715 cm distance
        mock_time.time.side_effect = [1.0, 1.0, 1.0, 1.0001]
        mock_time.sleep = MagicMock()  # Mock sleep calls

        sensor = UltrasonicSensor()
        distance = sensor._get_single_distance()

        # Expected: (0.0001 * 34300) / 2 = 1.715, rounded to 1.71
        assert distance == 1.71

        # Verify trigger pulse sequence
        expected_calls = [
            call(5, mock_gpio.LOW),  # Initialization
            call(5, mock_gpio.LOW),  # Trigger start
            call(5, mock_gpio.HIGH),  # Trigger pulse
            call(5, mock_gpio.LOW),  # Trigger end
        ]
        mock_gpio.output.assert_has_calls(expected_calls)

    def test_single_distance_timeout(self, mock_gpio: MagicMock, mock_time: MagicMock) -> None:
        """Test single distance measurement with timeout."""
        # Simulate timeout condition
        mock_gpio.input.return_value = mock_gpio.LOW
        mock_time.time.side_effect = [1.0, 1.6]  # Timeout after 0.6 seconds

        sensor = UltrasonicSensor()
        distance = sensor._get_single_distance()

        assert distance == -1.0

    def test_outlier_detection(self, mock_gpio: MagicMock) -> None:
        """Test outlier detection logic."""
        sensor = UltrasonicSensor(outlier_threshold=3.0)

        # No reference reading yet
        assert not sensor._is_outlier(25.0)

        # Set reference and test within threshold
        sensor.last_stable_reading = 25.0
        sensor.readings_buffer.extend([24.0, 25.0, 26.0])  # Buffer size >= 3
        assert not sensor._is_outlier(27.0)  # Within 3.0 cm

        # Test exceeding threshold
        assert sensor._is_outlier(30.0)  # Exceeds 3.0 cm

        # Test adaptive threshold with small buffer
        sensor.readings_buffer.clear()
        sensor.readings_buffer.extend([24.0, 25.0])  # Buffer size < 3
        # Should use adaptive threshold (3.0 * 2 = 6.0)
        assert not sensor._is_outlier(30.0)  # Within 6.0 cm

    def test_get_distance_successful(self, mock_gpio: MagicMock, mock_time: MagicMock) -> None:
        """Test successful distance measurement with filtering."""
        sensor = UltrasonicSensor(sample_count=3)

        with patch.object(sensor, "_get_single_distance") as mock_single:
            # Return multiple valid readings
            mock_single.side_effect = [25.0, 24.5, 25.5]

            distance = sensor.get_distance()

            assert distance > 0
            assert len(sensor.readings_buffer) == 1
            assert sensor.last_stable_reading is not None

    def test_get_distance_no_readings(
        self, mock_gpio: MagicMock, mock_time: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test distance measurement when no valid readings are available."""
        sensor = UltrasonicSensor(sample_count=3)

        with patch.object(sensor, "_get_single_distance") as mock_single:
            mock_single.return_value = -1.0  # All readings fail

            with caplog.at_level(logging.WARNING):
                distance = sensor.get_distance()

            assert distance == -1.0
            assert "No valid readings" in caplog.text

    def test_get_distance_single_reading(
        self, mock_gpio: MagicMock, mock_time: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test distance measurement with only one valid reading."""
        sensor = UltrasonicSensor(sample_count=3)

        with patch.object(sensor, "_get_single_distance") as mock_single:
            mock_single.side_effect = [-1.0, 25.0, -1.0, -1.0, -1.0, -1.0]

            with caplog.at_level(logging.DEBUG):
                distance = sensor.get_distance()

            assert distance == 25.0
            assert "Using single reading" in caplog.text

    def test_moving_average_buffer(self, mock_gpio: MagicMock) -> None:
        """Test that the moving average buffer works correctly."""
        sensor = UltrasonicSensor(filter_size=3)

        with patch.object(sensor, "_get_single_distance") as mock_single:
            mock_single.return_value = 25.0

            # Take multiple measurements
            for _ in range(5):
                sensor.get_distance()

            # Buffer should respect maxlen
            assert len(sensor.readings_buffer) == 3
            assert sensor.readings_buffer.maxlen == 3

    def test_cleanup(self, mock_gpio: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test sensor cleanup."""
        sensor = UltrasonicSensor()

        with caplog.at_level(logging.INFO):
            sensor.cleanup()

        assert "cleanup complete" in caplog.text
