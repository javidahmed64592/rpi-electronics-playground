"""Ultrasonic sensor control module for HC-SR04."""

import logging
import time

from RPi import GPIO

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


class UltrasonicSensor:
    """Class for controlling an HC-SR04 ultrasonic sensor."""

    def __init__(self, trig_pin: int = 5, echo_pin: int = 6) -> None:
        """Initialize the ultrasonic sensor.

        :param int trig_pin: GPIO pin for trigger signal.
        :param int echo_pin: GPIO pin for echo signal.
        """
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin

        self._initialize_sensor()

    def _initialize_sensor(self) -> None:
        """Initialize the sensor GPIO pins."""
        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.trig_pin, GPIO.OUT)
            GPIO.setup(self.echo_pin, GPIO.IN)

            # Ensure trigger is low initially
            GPIO.output(self.trig_pin, GPIO.LOW)

            logger.info("Ultrasonic sensor initialized on pins TRIG=%d, ECHO=%d", self.trig_pin, self.echo_pin)
        except Exception:
            logger.exception("Failed to initialize ultrasonic sensor!")
            raise

    def get_distance(self) -> float:
        """Measure distance using the ultrasonic sensor.

        :return: Distance in centimeters.
        :rtype: float
        """
        try:
            # Send trigger pulse
            GPIO.output(self.trig_pin, GPIO.LOW)
            time.sleep(0.000002)

            GPIO.output(self.trig_pin, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(self.trig_pin, GPIO.LOW)

            # Wait for echo response
            pulse_start = time.time()
            timeout_start = pulse_start

            # Wait for echo to go HIGH (start of return signal)
            while GPIO.input(self.echo_pin) == GPIO.LOW:
                pulse_start = time.time()
                # Timeout after 1 second to prevent infinite loop
                if pulse_start - timeout_start > 1.0:
                    logger.warning("Timeout waiting for echo signal start")
                    return -1.0

            # Wait for echo to go LOW (end of return signal)
            pulse_end = time.time()
            timeout_end = pulse_end

            while GPIO.input(self.echo_pin) == GPIO.HIGH:
                pulse_end = time.time()
                # Timeout after 1 second to prevent infinite loop
                if pulse_end - timeout_end > 1.0:
                    logger.warning("Timeout waiting for echo signal end")
                    return -1.0

            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            # Speed of sound is 343 m/s = 34300 cm/s
            # Distance = (Time x Speed) / 2 (divide by 2 for round trip)
            distance = (pulse_duration * 34300) / 2

            return round(distance, 2)

        except Exception:
            logger.exception("Error measuring distance!")
            return -1.0

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            logger.info("Ultrasonic sensor cleanup complete.")
        except Exception:
            logger.exception("Error during ultrasonic sensor cleanup!")


def debug() -> None:
    """Demonstrate ultrasonic sensor functionality."""
    sensor = UltrasonicSensor(trig_pin=5, echo_pin=6)

    try:
        logger.info("Starting distance measurements...")

        for i in range(10):
            distance = sensor.get_distance()
            if distance >= 0:
                logger.info("Measurement %d: Distance = %.2f cm", i + 1, distance)
            else:
                logger.warning("Measurement %d: Failed to get reading", i + 1)
            time.sleep(0.5)

        logger.info("Demo complete!")

    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        sensor.cleanup()
        GPIO.cleanup()
