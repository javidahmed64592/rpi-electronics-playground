"""Ultrasonic sensor control module for HC-SR04."""

import logging
import statistics
import time
from collections import deque

from RPi import GPIO

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


class UltrasonicSensor:
    """Class for controlling an HC-SR04 ultrasonic sensor with improved accuracy."""

    def __init__(
        self,
        trig_pin: int = 5,
        echo_pin: int = 6,
        sample_count: int = 5,
        filter_size: int = 10,
        outlier_threshold: float = 5.0,
    ) -> None:
        """Initialize the ultrasonic sensor.

        :param int trig_pin: GPIO pin for trigger signal.
        :param int echo_pin: GPIO pin for echo signal.
        :param int sample_count: Number of samples to average per reading.
        :param int filter_size: Size of moving average filter.
        :param float outlier_threshold: Maximum deviation (cm) for outlier rejection.
        """
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.sample_count = sample_count
        self.filter_size = filter_size
        self.outlier_threshold = outlier_threshold

        # Initialize moving average filter
        self.readings_buffer = deque(maxlen=filter_size)
        self.last_stable_reading = None

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

    def _get_single_distance(self) -> float:
        """Get a single distance measurement.

        :return: Distance in centimeters, or -1.0 if measurement failed.
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
                # Timeout after 0.5 seconds to prevent infinite loop
                if pulse_start - timeout_start > 0.5:
                    return -1.0

            # Wait for echo to go LOW (end of return signal)
            pulse_end = time.time()
            timeout_end = pulse_end

            while GPIO.input(self.echo_pin) == GPIO.HIGH:
                pulse_end = time.time()
                # Timeout after 0.5 seconds to prevent infinite loop
                if pulse_end - timeout_end > 0.5:
                    return -1.0

            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            # Speed of sound is 343 m/s = 34300 cm/s
            # Distance = (Time x Speed) / 2 (divide by 2 for round trip)
            distance = (pulse_duration * 34300) / 2

            return round(distance, 2)

        except Exception:
            return -1.0

    def _is_outlier(self, reading: float) -> bool:
        """Check if a reading is an outlier.

        :param float reading: The reading to check.
        :return: True if reading is an outlier.
        :rtype: bool
        """
        if self.last_stable_reading is None:
            return False

        deviation = abs(reading - self.last_stable_reading)
        return deviation > self.outlier_threshold

    def get_distance(self) -> float:
        """Measure distance using the ultrasonic sensor with improved accuracy.

        Uses multiple samples, outlier rejection, and moving average filtering
        to provide more stable and accurate readings.

        :return: Distance in centimeters.
        :rtype: float
        """
        try:
            # Take multiple samples and filter out bad readings
            valid_readings = []

            for _ in range(self.sample_count * 2):  # Take extra samples for filtering
                reading = self._get_single_distance()

                if reading > 0:  # Valid reading
                    # Check for outliers only if we have a reference
                    if not self._is_outlier(reading):
                        valid_readings.append(reading)

                    # If we have enough good readings, break early
                    if len(valid_readings) >= self.sample_count:
                        break

                # Small delay between samples
                time.sleep(0.01)

            # If we don't have enough valid readings, return error
            if len(valid_readings) < 2:
                logger.warning("Insufficient valid readings for distance measurement")
                return -1.0

            # Calculate median of the samples (more robust than mean)
            filtered_distance = statistics.median(valid_readings)

            # Add to moving average buffer
            self.readings_buffer.append(filtered_distance)

            # Calculate moving average
            if len(self.readings_buffer) >= 3:  # Need at least 3 readings for stability
                smoothed_distance = statistics.mean(self.readings_buffer)
                self.last_stable_reading = smoothed_distance
                return round(smoothed_distance, 1)
            else:
                # Not enough readings in buffer yet, return filtered reading
                self.last_stable_reading = filtered_distance
                return round(filtered_distance, 1)

        except Exception:
            logger.exception("Error measuring distance!")
            return -1.0

    def get_distance_with_quality(self) -> tuple[float, str]:
        """Get distance measurement with quality indicator.

        :return: Tuple of (distance, quality) where quality is 'excellent', 'good', 'fair', or 'poor'.
        :rtype: tuple[float, str]
        """
        distance = self.get_distance()

        if distance < 0:
            return distance, "poor"

        # Determine quality based on buffer size and reading stability
        buffer_size = len(self.readings_buffer)

        if buffer_size >= self.filter_size:
            # Calculate variance of recent readings for stability assessment
            if len(self.readings_buffer) > 1:
                variance = statistics.variance(self.readings_buffer)
                if variance < 0.5:
                    quality = "excellent"
                elif variance < 2.0:
                    quality = "good"
                else:
                    quality = "fair"
            else:
                quality = "good"
        elif buffer_size >= 3:
            quality = "fair"
        else:
            quality = "poor"

        return distance, quality

    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            logger.info("Ultrasonic sensor cleanup complete.")
        except Exception:
            logger.exception("Error during ultrasonic sensor cleanup!")


def debug() -> None:
    """Demonstrate ultrasonic sensor functionality with accuracy improvements."""
    sensor = UltrasonicSensor(trig_pin=5, echo_pin=6, sample_count=3, filter_size=5)

    try:
        logger.info("Starting enhanced distance measurements...")
        logger.info(
            "Using %d samples per reading with %d-point moving average", sensor.sample_count, sensor.filter_size
        )

        for i in range(15):
            distance, quality = sensor.get_distance_with_quality()
            if distance >= 0:
                logger.info("Measurement %d: Distance = %.1f cm (Quality: %s)", i + 1, distance, quality)
            else:
                logger.warning("Measurement %d: Failed to get reading", i + 1)
            time.sleep(1.0)

        logger.info("Demo complete!")

    except KeyboardInterrupt:
        logger.info("Exiting...")
    finally:
        sensor.cleanup()
        GPIO.cleanup()
