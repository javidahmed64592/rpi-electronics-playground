"""Base component class for all electronic components in the library."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from types import TracebackType
from typing import TypeVar

from RPi import GPIO
from template_python.logging_setup import setup_default_logging

T = TypeVar("T", bound="BaseElectronicsComponent")
setup_default_logging()

logger = logging.getLogger(__name__)


class BaseElectronicsComponent(ABC):
    """Base class for all electronic components providing standard patterns."""

    def __init__(self, component_name: str) -> None:
        """Initialize the base component.

        :param str component_name: Name of the component for logging purposes.
        """
        self.component_name = component_name
        self.is_initialized = False

        try:
            self._initialize_component()
            self.is_initialized = True
            logger.info("%s initialized successfully", self.component_name)
        except Exception as e:
            logger.exception("Failed to initialize %s", self.component_name)
            error_msg = f"Failed to initialize {self.component_name}: {e}"
            raise RuntimeError(error_msg) from e

    @abstractmethod
    def _initialize_component(self) -> None:
        """Initialize the specific component. Must be implemented by subclasses."""

    def _setup_gpio_pin(
        self,
        pin: int,
        mode: int,
        initial: int | None = None,
    ) -> None:
        """Set up a GPIO pin with proper error handling.

        :param int pin: The GPIO pin number.
        :param int mode: The pin mode (GPIO.IN or GPIO.OUT).
        :param int initial: Initial state for output pins (optional).
        """
        try:
            GPIO.setup(pin, mode)
            if mode == GPIO.OUT and initial is not None:
                GPIO.output(pin, initial)
            logger.debug("GPIO pin %d configured as %s", pin, "OUTPUT" if mode == GPIO.OUT else "INPUT")
        except Exception:
            logger.exception("Failed to setup GPIO pin %d", pin)
            raise

    def _ensure_gpio_mode_set(self) -> None:
        """Ensure GPIO mode is set to BCM if not already set."""
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
            logger.debug("GPIO mode set to BCM")

    def cleanup(self) -> None:
        """Clean up component resources."""
        if not self.is_initialized:
            logger.debug("Component %s was not initialized, skipping cleanup", self.component_name)
            return

        try:
            # Allow subclass-specific cleanup
            self._cleanup_component()

            # Clean up all GPIO pins
            GPIO.cleanup()

            self.is_initialized = False
            logger.info("%s cleanup complete", self.component_name)

        except Exception:
            logger.exception("Error during %s cleanup", self.component_name)
            raise

    @abstractmethod
    def _cleanup_component(self) -> None:
        """Perform component-specific cleanup. Override in subclasses if needed."""
        # Default implementation does nothing - subclasses can override

    def __enter__(self: T) -> T:
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc_val: Exception | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()
