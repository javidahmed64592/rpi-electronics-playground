"""Stepper motor control module for 28BYJ-48 with ULN2003 driver."""

import time

from RPi import GPIO

from .base_component import BaseElectronicsComponent


class StepperMotor(BaseElectronicsComponent):
    """Class for controlling a 28BYJ-48 stepper motor with ULN2003 driver."""

    def __init__(
        self,
        motor_pins: tuple[int, int, int, int] = (18, 23, 24, 25),
        rpm: int = 15,
        steps_per_revolution: int = 2048,
    ) -> None:
        """Initialize the stepper motor.

        :param tuple[int, int, int, int] motor_pins: GPIO pins for motor control (IN1, IN2, IN3, IN4).
        :param int rpm: Rotations per minute.
        :param int steps_per_revolution: Number of steps for a full revolution.
        """
        self.motor_pins = motor_pins
        self.rpm = rpm
        self.steps_per_revolution = steps_per_revolution
        self.step_speed = (60 / rpm) / steps_per_revolution

        super().__init__("StepperMotor")

    def _initialize_component(self) -> None:
        """Initialize the motor GPIO pins."""
        GPIO.setwarnings(False)
        self._ensure_gpio_mode_set()

        for pin in self.motor_pins:
            self._setup_gpio_pin(pin, GPIO.OUT, GPIO.LOW)

        self.logger.info(
            "Stepper motor initialized on pins %s at %d RPM",
            self.motor_pins,
            self.rpm,
        )

    def _step_clockwise(self) -> None:
        """Execute one step in clockwise direction."""
        for j in range(4):
            for i in range(4):
                GPIO.output(self.motor_pins[i], 0x99 >> j & (0x08 >> i))
            time.sleep(self.step_speed)

    def _step_counterclockwise(self) -> None:
        """Execute one step in counterclockwise direction."""
        for j in range(4):
            for i in range(4):
                GPIO.output(self.motor_pins[i], 0x99 << j & (0x80 >> i))
            time.sleep(self.step_speed)

    def rotate_clockwise(self, steps: int) -> None:
        """Rotate the motor clockwise for a specified number of steps.

        :param int steps: Number of steps to rotate.
        """
        try:
            self.logger.info("Rotating motor %d steps clockwise", steps)
            for _ in range(steps):
                self._step_clockwise()
        except Exception:
            self.logger.exception("Error during clockwise rotation!")
            raise

    def rotate_counterclockwise(self, steps: int) -> None:
        """Rotate the motor counterclockwise for a specified number of steps.

        :param int steps: Number of steps to rotate.
        """
        try:
            self.logger.info("Rotating motor %d steps counterclockwise", steps)
            for _ in range(steps):
                self._step_counterclockwise()
        except Exception:
            self.logger.exception("Error during counterclockwise rotation!")
            raise

    def rotate_degrees_clockwise(self, degrees: float) -> None:
        """Rotate the motor clockwise for a specified number of degrees.

        :param float degrees: Number of degrees to rotate.
        """
        steps = int((degrees / 360) * self.steps_per_revolution)
        self.rotate_clockwise(steps)

    def rotate_degrees_counterclockwise(self, degrees: float) -> None:
        """Rotate the motor counterclockwise for a specified number of degrees.

        :param float degrees: Number of degrees to rotate.
        """
        steps = int((degrees / 360) * self.steps_per_revolution)
        self.rotate_counterclockwise(steps)

    def stop(self) -> None:
        """Stop the motor by setting all pins to LOW."""
        try:
            for pin in self.motor_pins:
                GPIO.output(pin, GPIO.LOW)
            self.logger.info("Motor stopped")
        except Exception:
            self.logger.exception("Error stopping motor!")

    def _cleanup_component(self) -> None:
        """Clean up stepper motor resources."""
        self.stop()


def debug() -> None:
    """Demonstrate stepper motor functionality with various movements."""
    with StepperMotor(rpm=10) as motor:  # Slower speed for demonstration
        try:
            motor.logger.info("Starting stepper motor demonstration...")

            # Test quarter revolution clockwise
            motor.logger.info("Quarter revolution clockwise...")
            motor.rotate_degrees_clockwise(90)
            time.sleep(1)

            # Test quarter revolution counterclockwise
            motor.logger.info("Quarter revolution counterclockwise...")
            motor.rotate_degrees_counterclockwise(90)
            time.sleep(1)

            # Test specific step count
            motor.logger.info("100 steps counterclockwise...")
            motor.rotate_counterclockwise(100)

            motor.logger.info("Demo complete!")

        except KeyboardInterrupt:
            motor.logger.info("Demo interrupted by user")
        except Exception:
            motor.logger.exception("Error during demonstration!")
