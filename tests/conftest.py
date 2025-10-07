"""Test configuration and fixtures for the rfid_servo_lock package."""

import sys
from unittest.mock import MagicMock


class MockPWM:
    """Mock PWM class for GPIO PWM functionality."""

    def __init__(self, pin: int, frequency: int) -> None:
        """Initialize mock PWM."""
        self.pin = pin
        self.frequency = frequency

    def start(self, duty_cycle: float) -> None:
        """Mock PWM start method."""
        pass

    def stop(self) -> None:
        """Mock PWM stop method."""
        pass

    def ChangeDutyCycle(self, duty_cycle: float) -> None:  # noqa: N802
        """Mock PWM duty cycle change method."""
        pass


class MockGPIO:
    """Mock GPIO module for testing."""

    # GPIO mode constants
    BCM = "BCM"
    BOARD = "BOARD"

    # Pin mode constants
    OUT = "OUT"
    IN = "IN"

    # Pin state constants
    HIGH = 1
    LOW = 0

    @staticmethod
    def getmode() -> str | None:
        """Mock getmode function - returns BCM by default."""
        return MockGPIO.BCM

    @staticmethod
    def setmode(mode: str) -> None:
        """Mock setmode function."""
        pass

    @staticmethod
    def setup(pin: int, mode: str) -> None:
        """Mock setup function."""
        pass

    @staticmethod
    def output(pin: int, state: int) -> None:
        """Mock output function."""
        pass

    @staticmethod
    def cleanup() -> None:
        """Mock cleanup function."""
        pass

    @staticmethod
    def PWM(pin: int, frequency: int) -> MockPWM:  # noqa: N802
        """Mock PWM function - returns MockPWM instance."""
        return MockPWM(pin, frequency)


class MockSMBus:
    """Mock SMBus class for I2C operations."""

    def __init__(self, bus_number: int) -> None:
        """Initialize mock SMBus."""
        self.bus_number = bus_number

    def write_byte(self, address: int, value: int) -> None:
        """Mock write_byte method."""
        pass

    def close(self) -> None:
        """Mock close method."""
        pass


mock_modules = {
    "RPi": MagicMock(),
    "RPi.GPIO": MockGPIO(),
    "smbus2": MagicMock(SMBus=MockSMBus),
}

for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module  # type: ignore[assignment]
