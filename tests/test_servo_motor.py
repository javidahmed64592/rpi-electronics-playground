"""Unit tests for the rpi_electronics_playground.servo_motor module."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rpi_electronics_playground.servo_motor import ServoMotor


@pytest.fixture
def mock_gpio() -> Generator[MagicMock, None, None]:
    """Fixture to mock GPIO module."""
    with patch("rpi_electronics_playground.servo_motor.GPIO") as mock:
        mock.getmode.return_value = None
        mock_pwm = MagicMock()
        mock.PWM.return_value = mock_pwm
        yield mock


@pytest.fixture
def mock_sleep() -> Generator[MagicMock, None, None]:
    """Fixture to mock time.sleep."""
    with patch("rpi_electronics_playground.servo_motor.time.sleep") as mock:
        yield mock


class TestServoMotor:
    """Unit tests for the ServoMotor class."""

    @pytest.mark.parametrize(
        ("value", "in_min", "in_max", "out_min", "out_max", "expected"),
        [
            # Basic mapping - 50% of input range should map to 50% of output range
            (50, 0, 100, 0, 180, 90),
            # Edge case - minimum input should map to minimum output
            (0, 0, 100, 0, 180, 0),
            # Edge case - maximum input should map to maximum output
            (100, 0, 100, 0, 180, 180),
            # Different ranges - test with pulse width mapping
            (1500, 500, 2500, 0, 100, 50),
        ],
    )
    def test_map_value(
        self,
        value: int,
        in_min: int,
        in_max: int,
        out_min: int,
        out_max: int,
        expected: int,
    ) -> None:
        """Test the _map_value static method with various input combinations."""
        assert ServoMotor._map_value(value, in_min, in_max, out_min, out_max) == expected

    def test_set_angle(self, mock_sleep: MagicMock, mock_gpio: MagicMock) -> None:
        """Test setting servo angle."""
        mock_gpio.getmode.return_value = None
        mock_pwm = MagicMock()
        mock_gpio.PWM.return_value = mock_pwm

        servo = ServoMotor()
        servo._set_angle(90)

        mock_pwm.ChangeDutyCycle.assert_called()
        mock_sleep.assert_called_with(0.5)

    @pytest.mark.parametrize(
        ("initial_locked_state", "expected_locked_state", "should_call_pwm"),
        [
            # Test locking when unlocked - should change state and call PWM
            (False, True, True),
            # Test locking when already locked - should not change state or call PWM
            (True, True, False),
        ],
    )
    def test_lock(
        self,
        initial_locked_state: bool,
        expected_locked_state: bool,
        should_call_pwm: bool,
        mock_sleep: MagicMock,
        mock_gpio: MagicMock,
    ) -> None:
        """Test locking mechanism with different initial states."""
        mock_gpio.getmode.return_value = None
        mock_pwm = MagicMock()
        mock_gpio.PWM.return_value = mock_pwm

        servo = ServoMotor()
        servo.is_locked = initial_locked_state
        initial_call_count = mock_pwm.ChangeDutyCycle.call_count

        servo._lock()

        assert servo.is_locked == expected_locked_state
        if should_call_pwm:
            assert mock_pwm.ChangeDutyCycle.call_count > initial_call_count
        else:
            assert mock_pwm.ChangeDutyCycle.call_count == initial_call_count

    @pytest.mark.parametrize(
        ("initial_locked_state", "expected_locked_state", "should_call_pwm"),
        [
            # Test unlocking when locked - should change state and call PWM
            (True, False, True),
            # Test unlocking when already unlocked - should not change state or call PWM
            (False, False, False),
        ],
    )
    def test_unlock(
        self,
        initial_locked_state: bool,
        expected_locked_state: bool,
        should_call_pwm: bool,
        mock_sleep: MagicMock,
        mock_gpio: MagicMock,
    ) -> None:
        """Test unlocking mechanism with different initial states."""
        mock_gpio.getmode.return_value = None
        mock_pwm = MagicMock()
        mock_gpio.PWM.return_value = mock_pwm

        servo = ServoMotor()
        servo.is_locked = initial_locked_state
        initial_call_count = mock_pwm.ChangeDutyCycle.call_count

        servo._unlock()

        assert servo.is_locked == expected_locked_state
        if should_call_pwm:
            assert mock_pwm.ChangeDutyCycle.call_count > initial_call_count
        else:
            assert mock_pwm.ChangeDutyCycle.call_count == initial_call_count

    @pytest.mark.parametrize(
        ("initial_locked_state", "expected_locked_state"),
        [
            # Test toggle from locked - should change to unlocked
            (True, False),
            # Test toggle from unlocked - should change to locked
            (False, True),
        ],
    )
    def test_toggle(
        self,
        initial_locked_state: bool,
        expected_locked_state: bool,
        mock_sleep: MagicMock,
        mock_gpio: MagicMock,
    ) -> None:
        """Test toggle functionality from different initial states."""
        mock_gpio.getmode.return_value = None
        mock_pwm = MagicMock()
        mock_gpio.PWM.return_value = mock_pwm

        servo = ServoMotor()
        servo.is_locked = initial_locked_state

        servo.toggle()

        assert servo.is_locked == expected_locked_state

    def test_cleanup(self, mock_gpio: MagicMock) -> None:
        """Test cleanup method."""
        mock_gpio.getmode.return_value = None
        mock_pwm = MagicMock()
        mock_gpio.PWM.return_value = mock_pwm

        servo = ServoMotor()
        servo.cleanup()

        mock_pwm.stop.assert_called_once()
        assert servo.pwm is None
