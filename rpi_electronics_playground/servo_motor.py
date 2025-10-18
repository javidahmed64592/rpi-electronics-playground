"""Servo motor control module for lock/unlock operations."""

import time

from RPi import GPIO

from rpi_electronics_playground.base_component import BaseElectronicsComponent


class ServoMotor(BaseElectronicsComponent):
    """Class for controlling a servo motor as a lock mechanism."""

    def __init__(
        self,
        pin: int = 18,
        locked_angle: int = 0,
        unlocked_angle: int = 90,
        frequency: int = 50,
        min_pulse: int = 500,
        max_pulse: int = 2500,
    ) -> None:
        """Initialize the servo lock.

        :param int pin: GPIO pin number for servo control.
        :param int locked_angle: Angle for locked position (0-180 degrees).
        :param int unlocked_angle: Angle for unlocked position (0-180 degrees).
        :param int frequency: PWM frequency in Hz.
        :param int min_pulse: Minimum pulse width in microseconds.
        :param int max_pulse: Maximum pulse width in microseconds.
        """
        self.pin = pin
        self.locked_angle = locked_angle
        self.unlocked_angle = unlocked_angle
        self.frequency = frequency
        self.min_pulse = min_pulse
        self.max_pulse = max_pulse
        self.pwm: GPIO.PWM | None = None
        self.is_locked = True

        super().__init__("ServoMotor")

    def _initialize_component(self) -> None:
        """Initialize the servo motor hardware."""
        self._ensure_gpio_mode_set()
        self._setup_gpio_pin(self.pin, GPIO.OUT, GPIO.LOW)

        if pwm := GPIO.PWM(self.pin, self.frequency):
            self.pwm = pwm
            self.pwm.start(0)

        # Move to locked position
        self._lock()

    @staticmethod
    def _map_value(
        value: int,
        in_min: int,
        in_max: int,
        out_min: int,
        out_max: int,
    ) -> int:
        """Map a value from one range to another."""
        return int((out_max - out_min) * (value - in_min) / (in_max - in_min) + out_min)

    def _set_angle(self, angle: int) -> None:
        """Set the servo to a specific angle.

        :param int angle: Target angle (0-180 degrees).
        """
        angle = max(0, min(180, angle))
        pulse_width = self._map_value(angle, 0, 180, self.min_pulse, self.max_pulse)
        duty_cycle = self._map_value(pulse_width, 0, 20000, 0, 100)

        if self.pwm:
            self.pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.5)

    def _lock(self) -> None:
        """Lock the mechanism by moving to locked position."""
        if not self.is_locked:
            self._set_angle(self.locked_angle)
            self.is_locked = True

    def _unlock(self) -> None:
        """Unlock the mechanism by moving to unlocked position."""
        if self.is_locked:
            self._set_angle(self.unlocked_angle)
            self.is_locked = False

    def toggle(self) -> None:
        """Toggle between locked and unlocked states."""
        if self.is_locked:
            self._unlock()
        else:
            self._lock()

    def _cleanup_component(self) -> None:
        """Clean up PWM resources."""
        if self.pwm:
            self.pwm.stop()
            self.pwm = None


def debug() -> None:
    """Demonstrate servo lock functionality."""
    with ServoMotor() as servo_lock:
        try:
            while True:
                command = input("Enter command (lock/unlock/toggle/quit): ").strip().lower()

                if command == "lock":
                    servo_lock._lock()
                elif command == "unlock":
                    servo_lock._unlock()
                elif command == "toggle":
                    servo_lock.toggle()
                elif command in ["quit", "q", "exit"]:
                    break
                else:
                    servo_lock.logger.warning("Invalid command. Use: lock, unlock, toggle, or quit")

        except KeyboardInterrupt:
            servo_lock.logger.info("Exiting...")
