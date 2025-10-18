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
        assert component.logger.name == "rpi_electronics_playground.TestDevice"

    def test_init_with_gpio_setup(self, mock_gpio: MagicMock) -> None:
        """Test component initialization sets up GPIO mode."""
        TestComponent()

        mock_gpio.getmode.assert_called_once()
        mock_gpio.setmode.assert_called_once_with(mock_gpio.BCM)

    def test_gpio_pin_registration(self, mock_gpio: MagicMock) -> None:
        """Test GPIO pin registration functionality."""
        component = TestComponent()

        # Register some pins
        component._register_gpio_pin(18)
        component._register_gpio_pin(24)

        assert component.gpio_pins == [18, 24]

    def test_cleanup(self, mock_gpio: MagicMock) -> None:
        """Test component cleanup functionality."""
        component = TestComponent()
        component._register_gpio_pin(18)
        component._register_gpio_pin(24)

        component.cleanup()

        mock_gpio.cleanup.assert_called_once()
