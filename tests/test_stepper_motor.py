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

    def test_initialization(self, mock_gpio: MagicMock) -> None:
        """Test stepper motor initialization with default and custom parameters."""
        mock_gpio.getmode.return_value = None

        # Test default parameters
        motor = StepperMotor()

        assert motor.component_name == "StepperMotor"
        assert motor.is_initialized is True
        assert motor.motor_pins == (18, 23, 24, 25)
        assert motor.rpm == 15  # noqa: PLR2004
        assert motor.steps_per_revolution == 2048  # noqa: PLR2004
        assert motor.step_speed == (60 / 15) / 2048

        # Verify GPIO setup was called
        mock_gpio.setmode.assert_called_with(mock_gpio.BCM)

        # Check that each pin was set up correctly
        expected_setup_calls = [call(pin, mock_gpio.OUT) for pin in (18, 23, 24, 25)]
        mock_gpio.setup.assert_has_calls(expected_setup_calls)

        # Check that each pin was set to LOW initially
        expected_output_calls = [call(pin, mock_gpio.LOW) for pin in (18, 23, 24, 25)]
        mock_gpio.output.assert_has_calls(expected_output_calls)

    def test_rotate_clockwise(self, mock_gpio: MagicMock, mock_sleep: MagicMock) -> None:
        """Test clockwise rotation."""
        motor = StepperMotor()
        motor.rotate_clockwise(5)

        # Verify that GPIO.output was called for the stepping sequence
        assert mock_gpio.output.call_count >= 5 * 4 * 4  # 5 steps * 4 phases * 4 pins per phase
        mock_sleep.assert_called()

    def test_rotate_counterclockwise(self, mock_gpio: MagicMock, mock_sleep: MagicMock) -> None:
        """Test counterclockwise rotation."""
        motor = StepperMotor()
        motor.rotate_counterclockwise(3)

        # Verify that GPIO.output was called for the stepping sequence
        assert mock_gpio.output.call_count >= 3 * 4 * 4  # 3 steps * 4 phases * 4 pins per phase
        mock_sleep.assert_called()

    def test_rotate_degrees_clockwise(self, mock_gpio: MagicMock, mock_sleep: MagicMock) -> None:
        """Test degree-based clockwise rotation."""
        motor = StepperMotor()
        motor.rotate_degrees_clockwise(90)

        # 90 degrees = 1/4 revolution = 2048/4 = 512 steps
        expected_steps = int((90 / 360) * 2048)
        assert mock_gpio.output.call_count >= expected_steps * 4 * 4

    def test_rotate_degrees_counterclockwise(self, mock_gpio: MagicMock, mock_sleep: MagicMock) -> None:
        """Test degree-based counterclockwise rotation."""
        motor = StepperMotor()
        motor.rotate_degrees_counterclockwise(90)

        # 90 degrees = 1/4 revolution = 2048/4 = 512 steps
        expected_steps = int((90 / 360) * 2048)
        assert mock_gpio.output.call_count >= expected_steps * 4 * 4

    def test_stop(self, mock_gpio: MagicMock) -> None:
        """Test motor stop functionality."""
        motor = StepperMotor()
        mock_gpio.output.reset_mock()  # Reset call count from initialization

        motor.stop()

        # Verify all pins are set to LOW
        expected_calls = [call(pin, mock_gpio.LOW) for pin in motor.motor_pins]
        mock_gpio.output.assert_has_calls(expected_calls)

    def test_cleanup(self, mock_gpio: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
        """Test motor cleanup."""
        motor = StepperMotor()

        with caplog.at_level(logging.INFO):
            motor.cleanup()

        assert "cleanup complete" in caplog.text
