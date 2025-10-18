"""Base component class for all electronic components in the library."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from types import TracebackType
from typing import TypeVar

from RPi import GPIO

T = TypeVar("T", bound="BaseElectronicsComponent")


class BaseElectronicsComponent(ABC):
    """Base class for all electronic components providing standard patterns."""

    def __init__(self, component_name: str) -> None:
        """Initialize the base component.

        :param str component_name: Name of the component for logging purposes.
        """
        self.component_name = component_name
        self.logger = self._setup_logger()
        self.is_initialized = False
        self._gpio_pins_used: set[int] = set()

        try:
            self._initialize_component()
            self.is_initialized = True
            self.logger.info("%s initialized successfully", self.component_name)
        except Exception as e:
            self.logger.exception("Failed to initialize %s", self.component_name)
            error_msg = f"Failed to initialize {self.component_name}: {e}"
            raise RuntimeError(error_msg) from e

    def _setup_logger(self) -> logging.Logger:
        """Set up logger for the component.

        :return logging.Logger: Configured logger instance.
        """
        # Create logger for this component
        logger = logging.getLogger(f"rpi_electronics_playground.{self.component_name.lower()}")

        # Only add handler if it doesn't already have one (avoid duplicates)
        if not logger.handlers:
            # Create formatter
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]"
            )

            # Create console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)

        return logger

    @abstractmethod
    def _initialize_component(self) -> None:
        """Initialize the specific component. Must be implemented by subclasses."""

    def _register_gpio_pin(self, pin: int) -> None:
        """Register a GPIO pin as being used by this component.

        :param int pin: The GPIO pin number.
        """
        self._gpio_pins_used.add(pin)

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
            self._register_gpio_pin(pin)
            self.logger.debug("GPIO pin %d configured as %s", pin, "OUTPUT" if mode == GPIO.OUT else "INPUT")
        except Exception:
            self.logger.exception("Failed to setup GPIO pin %d", pin)
            raise

    def _ensure_gpio_mode_set(self) -> None:
        """Ensure GPIO mode is set to BCM if not already set."""
        if GPIO.getmode() is None:
            GPIO.setmode(GPIO.BCM)
            self.logger.debug("GPIO mode set to BCM")

    def cleanup(self) -> None:
        """Clean up component resources including GPIO pins."""
        if not self.is_initialized:
            self.logger.debug("Component %s was not initialized, skipping cleanup", self.component_name)
            return

        try:
            # Allow subclass-specific cleanup
            self._cleanup_component()

            # Clean up GPIO pins used by this component
            if self._gpio_pins_used:
                for pin in self._gpio_pins_used:
                    try:
                        GPIO.setup(pin, GPIO.IN)  # Set to safe input mode
                        GPIO.output(pin, GPIO.LOW)  # Ensure low output
                    except Exception as pin_error:
                        self.logger.warning("Failed to cleanup GPIO pin %d: %s", pin, pin_error)

                self.logger.debug("Cleaned up GPIO pins: %s", sorted(self._gpio_pins_used))

            self.is_initialized = False
            self.logger.info("%s cleanup complete", self.component_name)

        except Exception:
            self.logger.exception("Error during %s cleanup", self.component_name)
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
