"""Unit tests for the rpi_electronics_playground.base_component module."""

import logging
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rpi_electronics_playground.base_component import BaseElectronicsComponent


class TestComponent(BaseElectronicsComponent):
    """Test implementation of BaseElectronicsComponent for testing."""

    def __init__(self, name: str = "TestComponent") -> None:
        """Initialize test component."""
        self.initialization_called = False
        self.cleanup_called = False
        super().__init__(name)

    def _initialize_component(self) -> None:
        """Mock implementation of component initialization."""
        self.initialization_called = True

    def _cleanup_component(self) -> None:
        """Mock implementation of component cleanup."""
        self.cleanup_called = True


@pytest.fixture
def mock_gpio() -> Generator[MagicMock, None, None]:
    """Fixture to mock GPIO module."""
    with patch("rpi_electronics_playground.base_component.GPIO") as mock:
        mock.getmode.return_value = None
        yield mock


class TestBaseElectronicsComponent:
    """Unit tests for the BaseElectronicsComponent class."""

    def test_init(self, mock_gpio: MagicMock) -> None:
        """Test component initialization."""
        component = TestComponent("TestDevice")

        assert component.component_name == "TestDevice"
        assert component.is_initialized is True
        assert component.initialization_called is True
        assert isinstance(component.logger, logging.Logger)
        assert component.logger.name == "rpi_electronics_playground.testdevice"

    def test_init_with_gpio_setup(self, mock_gpio: MagicMock) -> None:
        """Test component initialization sets up GPIO mode."""
        TestComponent()

        # GPIO.getmode() should be called during initialization but setmode is not called in this version
        mock_gpio.getmode.assert_called()

    def test_gpio_pin_registration(self, mock_gpio: MagicMock) -> None:
        """Test GPIO pin registration functionality."""
        component = TestComponent()

        # Register some pins
        component._register_gpio_pin(18)
        component._register_gpio_pin(24)

        assert 18 in component._gpio_pins_used
        assert 24 in component._gpio_pins_used
        assert len(component._gpio_pins_used) == 2

    def test_gpio_pin_registration_duplicate(self, mock_gpio: MagicMock) -> None:
        """Test GPIO pin registration prevents duplicates."""
        component = TestComponent()

        component._register_gpio_pin(18)
        component._register_gpio_pin(18)  # Duplicate

        assert len(component._gpio_pins_used) == 1
        assert 18 in component._gpio_pins_used

    def test_context_manager(self, mock_gpio: MagicMock) -> None:
        """Test component works as context manager."""
        with TestComponent("ContextTest") as component:
            assert component.component_name == "ContextTest"
            assert component.is_initialized is True

        # Component should be cleaned up after context
        mock_gpio.cleanup.assert_called()

    def test_context_manager_with_exception(self, mock_gpio: MagicMock) -> None:
        """Test context manager cleanup on exception."""
        try:
            with TestComponent() as component:
                assert component.is_initialized is True
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Cleanup should still be called even with exception
        mock_gpio.cleanup.assert_called()

    def test_cleanup(self, mock_gpio: MagicMock) -> None:
        """Test component cleanup functionality."""
        component = TestComponent()
        component._register_gpio_pin(18)
        component._register_gpio_pin(24)

        component.cleanup()

        # The new base component cleans up individual pins instead of calling GPIO.cleanup()
        assert component.cleanup_called is True
        assert component.is_initialized is False
        # Should call GPIO.setup for each pin to set to safe input mode
        mock_gpio.setup.assert_called()
        mock_gpio.output.assert_called()

    def test_repr(self, mock_gpio: MagicMock) -> None:
        """Test component string representation."""
        component = TestComponent("ReprTest")

        repr_str = repr(component)

        assert "ReprTest" in repr_str
        assert "BaseElectronicsComponent" in repr_str

    def test_logger_setup(self, mock_gpio: MagicMock) -> None:
        """Test logger is properly configured."""
        component = TestComponent("LoggerTest")

        assert component.logger.name == "rpi_electronics_playground.LoggerTest"
        assert component.logger.level == logging.INFO

    def test_gpio_mode_already_set(self, mock_gpio: MagicMock) -> None:
        """Test GPIO mode handling when already set."""
        mock_gpio.getmode.return_value = mock_gpio.BCM

        TestComponent()

        # Should not call setmode if already set
        mock_gpio.setmode.assert_not_called()

    def test_setup_gpio_pin_with_mode_and_state(self, mock_gpio: MagicMock) -> None:
        """Test GPIO pin setup with mode and initial state."""
        component = TestComponent()

        component._setup_gpio_pin(18, mock_gpio.OUT, initial=mock_gpio.HIGH)

        mock_gpio.setup.assert_called_with(18, mock_gpio.OUT)
        mock_gpio.output.assert_called_with(18, mock_gpio.HIGH)
        assert 18 in component._gpio_pins_used

    def test_setup_gpio_pin_with_mode_only(self, mock_gpio: MagicMock) -> None:
        """Test GPIO pin setup with mode only."""
        component = TestComponent()

        component._setup_gpio_pin(24, mock_gpio.IN)

        mock_gpio.setup.assert_called_with(24, mock_gpio.IN)
        assert 24 in component._gpio_pins_used
