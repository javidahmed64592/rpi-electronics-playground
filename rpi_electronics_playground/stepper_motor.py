"""Stepper motor control module for 28BYJ-48 with ULN2003 driver."""

import logging
import time

from RPi import GPIO

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


class StepperMotor:
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

        self._initialize_motor()

    def _initialize_motor(self) -> None:
        """Initialize the motor GPIO pins."""
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            for pin in self.motor_pins:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)  # Ensure all pins start LOW

            logger.info(
                "Stepper motor initialized on pins %s at %d RPM",
                self.motor_pins,
                self.rpm,
            )
        except Exception:
            logger.exception("Failed to initialize stepper motor!")
            raise

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
            logger.info("Rotating motor %d steps clockwise", steps)
            for _ in range(steps):
                self._step_clockwise()
        except Exception:
            logger.exception("Error during clockwise rotation!")
            raise

    def rotate_counterclockwise(self, steps: int) -> None:
        """Rotate the motor counterclockwise for a specified number of steps.

        :param int steps: Number of steps to rotate.
        """
        try:
            logger.info("Rotating motor %d steps counterclockwise", steps)
            for _ in range(steps):
                self._step_counterclockwise()
        except Exception:
            logger.exception("Error during counterclockwise rotation!")
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
            logger.info("Motor stopped")
        except Exception:
            logger.exception("Error stopping motor!")

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            self.stop()
            logger.info("Stepper motor cleanup complete.")
        except Exception:
            logger.exception("Error during stepper motor cleanup!")


def debug() -> None:
    """Demonstrate stepper motor functionality with various movements."""
    motor = StepperMotor(rpm=10)  # Slower speed for demonstration

    try:
        logger.info("Starting stepper motor demonstration...")

        # Test quarter revolution clockwise
        logger.info("Quarter revolution clockwise...")
        motor.rotate_degrees_clockwise(90)
        time.sleep(1)

        # Test quarter revolution counterclockwise
        logger.info("Quarter revolution counterclockwise...")
        motor.rotate_degrees_counterclockwise(90)
        time.sleep(1)

        # Test specific step count
        logger.info("100 steps counterclockwise...")
        motor.rotate_counterclockwise(100)

        logger.info("Demo complete!")

    except KeyboardInterrupt:
        logger.info("Demo interrupted by user")
    except Exception:
        logger.exception("Error during demonstration!")
    finally:
        motor.cleanup()
        GPIO.cleanup()
