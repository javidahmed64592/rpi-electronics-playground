"""Unit tests for the rpi_electronics_playground.stepper_motor module."""

import logging
from collections.abc import Generator
from unittest.mock import MagicMock, call, patch

import pytest

from rpi_electronics_playground.stepper_motor import StepperMotor


@pytest.fixture
def mock_gpio() -> Generator[MagicMock, None, None]:
    """Fixture to mock GPIO module."""
    with patch("rpi_electronics_playground.stepper_motor.GPIO") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_sleep() -> Generator[MagicMock, None, None]:
    """Fixture to mock time.sleep."""
    with patch("rpi_electronics_playground.stepper_motor.time.sleep") as mock:
        yield mock


class TestStepperMotor:
    """Unit tests for StepperMotor core functionality."""

    def test_rotate_clockwise(self, mock_gpio: MagicMock, mock_sleep: MagicMock) -> None:
        """Test clockwise rotation."""
        mock_gpio.getmode.return_value = None
        motor = StepperMotor()
        motor.rotate_clockwise(5)

        # Verify that GPIO.output was called for the stepping sequence
        assert mock_gpio.output.call_count >= 5 * 4 * 4  # 5 steps * 4 phases * 4 pins per phase
        mock_sleep.assert_called()

    def test_rotate_counterclockwise(self, mock_gpio: MagicMock, mock_sleep: MagicMock) -> None:
        """Test counterclockwise rotation."""
        mock_gpio.getmode.return_value = None
        motor = StepperMotor()
        motor.rotate_counterclockwise(3)

        # Verify that GPIO.output was called for the stepping sequence
        assert mock_gpio.output.call_count >= 3 * 4 * 4  # 3 steps * 4 phases * 4 pins per phase
        mock_sleep.assert_called()

    def test_rotate_degrees_clockwise(self, mock_gpio: MagicMock, mock_sleep: MagicMock) -> None:
        """Test degree-based clockwise rotation."""
        mock_gpio.getmode.return_value = None
        motor = StepperMotor()
        motor.rotate_degrees_clockwise(90)

        # 90 degrees = 1/4 revolution = 2048/4 = 512 steps
        expected_steps = int((90 / 360) * 2048)
        assert mock_gpio.output.call_count >= expected_steps * 4 * 4

    def test_rotate_degrees_counterclockwise(self, mock_gpio: MagicMock, mock_sleep: MagicMock) -> None:
        """Test degree-based counterclockwise rotation."""
        mock_gpio.getmode.return_value = None
        motor = StepperMotor()
        motor.rotate_degrees_counterclockwise(90)

        # 90 degrees = 1/4 revolution = 2048/4 = 512 steps
        expected_steps = int((90 / 360) * 2048)
        assert mock_gpio.output.call_count >= expected_steps * 4 * 4

    def test_stop(self, mock_gpio: MagicMock) -> None:
        """Test motor stop functionality."""
        mock_gpio.getmode.return_value = None
        motor = StepperMotor()
        mock_gpio.output.reset_mock()  # Reset call count from initialization

        motor.stop()

        # Verify all pins are set to LOW
        expected_calls = [call(pin, mock_gpio.LOW) for pin in motor.motor_pins]
        mock_gpio.output.assert_has_calls(expected_calls)

    def test_cleanup(self, mock_gpio: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test motor cleanup."""
        mock_gpio.getmode.return_value = None
        motor = StepperMotor()

        with caplog.at_level(logging.INFO):
            motor.cleanup()

        assert "cleanup complete" in caplog.text
