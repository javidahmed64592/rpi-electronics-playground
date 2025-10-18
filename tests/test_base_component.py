"""Unit tests for the rpi_electronics_playground.base_component module."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from rpi_electronics_playground.base_component import BaseElectronicsComponent


class MockComponent(BaseElectronicsComponent):
    """Test implementation of BaseElectronicsComponent for testing."""

    def __init__(self, name: str = "MockComponent") -> None:
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

    def test_initialization(self, mock_gpio: MagicMock) -> None:
        """Test component initialization."""
        component = MockComponent()

        assert component.is_initialized is True
        assert component.initialization_called is True
        assert component.component_name == "MockComponent"

    def test_cleanup(self, mock_gpio: MagicMock) -> None:
        """Test component cleanup functionality."""
        component = MockComponent()

        component.cleanup()

        # Should call component-specific cleanup and GPIO.cleanup()
        assert component.cleanup_called is True
        assert component.is_initialized is False
        mock_gpio.cleanup.assert_called_once()

    def test_gpio_mode_already_set(self, mock_gpio: MagicMock) -> None:
        """Test GPIO mode handling when already set."""
        mock_gpio.getmode.return_value = mock_gpio.BCM

        MockComponent()

        # Should not call setmode if already set
        mock_gpio.setmode.assert_not_called()

    def test_setup_gpio_pin_with_mode_and_state(self, mock_gpio: MagicMock) -> None:
        """Test GPIO pin setup with mode and initial state."""
        component = MockComponent()

        component._setup_gpio_pin(18, mock_gpio.OUT, initial=mock_gpio.HIGH)

        mock_gpio.setup.assert_called_with(18, mock_gpio.OUT)
        mock_gpio.output.assert_called_with(18, mock_gpio.HIGH)
        assert 18 in component._gpio_pins_used

    def test_setup_gpio_pin_with_mode_only(self, mock_gpio: MagicMock) -> None:
        """Test GPIO pin setup with mode only."""
        component = MockComponent()

        component._setup_gpio_pin(24, mock_gpio.IN)

        mock_gpio.setup.assert_called_with(24, mock_gpio.IN)
        assert 24 in component._gpio_pins_used
