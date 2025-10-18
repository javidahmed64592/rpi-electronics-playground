"""Ultrasonic sensor control module for HC-SR04."""

import statistics
import time
from collections import deque

from RPi import GPIO

from .base_component import BaseElectronicsComponent


class UltrasonicSensor(BaseElectronicsComponent):
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
        self.readings_buffer: deque[float] = deque(maxlen=filter_size)
        self.last_stable_reading: float | None = None

        super().__init__("UltrasonicSensor")

    def _initialize_component(self) -> None:
        """Initialize the sensor GPIO pins."""
        self._ensure_gpio_mode_set()
        self._setup_gpio_pin(self.trig_pin, GPIO.OUT, GPIO.LOW)
        self._setup_gpio_pin(self.echo_pin, GPIO.IN)

        self.logger.info("Ultrasonic sensor initialized on pins TRIG=%d, ECHO=%d", self.trig_pin, self.echo_pin)

    def _get_single_distance(self) -> float:
        """Get a single distance measurement.

        :return float: Distance in centimeters, or -1.0 if measurement failed.
        """
        timeout = 0.5  # seconds
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
                if pulse_start - timeout_start > timeout:
                    return -1.0

            # Wait for echo to go LOW (end of return signal)
            pulse_end = time.time()
            timeout_end = pulse_end

            while GPIO.input(self.echo_pin) == GPIO.HIGH:
                pulse_end = time.time()
                # Timeout after 0.5 seconds to prevent infinite loop
                if pulse_end - timeout_end > timeout:
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
        :return bool: True if reading is an outlier.
        """
        if self.last_stable_reading is None:
            return False

        # Be more lenient with outlier detection when we have few readings
        buffer_size = len(self.readings_buffer)
        if buffer_size < 3:  # noqa: PLR2004
            # Use a larger threshold when we don't have much data
            adaptive_threshold = self.outlier_threshold * 2
        else:
            adaptive_threshold = self.outlier_threshold

        deviation = abs(reading - self.last_stable_reading)
        return deviation > adaptive_threshold

    def get_distance(self) -> float:
        """Measure distance using the ultrasonic sensor with improved accuracy.

        Uses multiple samples, outlier rejection, and moving average filtering
        to provide more stable and accurate readings.

        :return float: Distance in centimeters.
        """
        try:
            # Take multiple samples and filter out bad readings
            valid_readings = []

            for _ in range(self.sample_count * 2):
                reading = self._get_single_distance()

                if reading > 0:  # Valid reading
                    # Check for outliers only if we have a reference
                    if not self._is_outlier(reading):
                        valid_readings.append(reading)
                    # Even outliers can be useful if we don't have many readings
                    elif len(valid_readings) < 2:  # noqa: PLR2004
                        valid_readings.append(reading)

                    if len(valid_readings) >= self.sample_count:
                        break

                # Small delay between samples
                time.sleep(0.01)

            if len(valid_readings) == 0:
                self.logger.warning("No valid readings for distance measurement")
                return -1.0

            if len(valid_readings) == 1:
                # Single reading - use it but mark as less reliable
                filtered_distance = valid_readings[0]
                self.logger.debug("Using single reading: %.1f cm", filtered_distance)
            else:
                # Multiple readings - use median for robustness
                filtered_distance = statistics.median(valid_readings)

            # Add to moving average buffer
            self.readings_buffer.append(filtered_distance)

            # Calculate moving average with more lenient requirements
            if len(self.readings_buffer) >= 2:  # noqa: PLR2004
                smoothed_distance = statistics.mean(self.readings_buffer)
                self.last_stable_reading = smoothed_distance
                return float(round(smoothed_distance, 1))

            # First reading - return as-is
            self.last_stable_reading = filtered_distance
            return float(round(filtered_distance, 1))

        except Exception:
            self.logger.exception("Error measuring distance!")
            return -1.0

    def _cleanup_component(self) -> None:
        """Clean up ultrasonic sensor resources."""
        # No specific cleanup needed for ultrasonic sensor


def debug() -> None:
    """Demonstrate ultrasonic sensor functionality with accuracy improvements."""
    with UltrasonicSensor(trig_pin=5, echo_pin=6, sample_count=3, filter_size=5) as sensor:
        try:
            sensor.logger.info("Starting enhanced distance measurements...")
            sensor.logger.info(
                "Using %d samples per reading with %d-point moving average", sensor.sample_count, sensor.filter_size
            )

            for i in range(15):
                distance = sensor.get_distance()
                if distance >= 0:
                    sensor.logger.info("Measurement %d: Distance = %.1f cm", i + 1, distance)
                else:
                    sensor.logger.warning("Measurement %d: Failed to get reading", i + 1)
                time.sleep(1.0)

            sensor.logger.info("Demo complete!")

        except KeyboardInterrupt:
            sensor.logger.info("Exiting...")
