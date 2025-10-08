"""Main application for the Raspberry Pi Electronics Playground."""

import logging
import time

from RPi import GPIO

from rpi_electronics_playground.lcd import LCD1602
from rpi_electronics_playground.ultrasonic_sensor import UltrasonicSensor

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


def run() -> None:
    """Run the Raspberry Pi Electronics Playground."""
    logger.info("Initializing Raspberry Pi Electronics Playground...")

    # Initialize LCD display
    lcd = LCD1602(address=0x27, backlight=True)
    lcd.clear()
    lcd.write(0, 0, "[STARTUP]")
    lcd.write(0, 1, "Initializing...")

    # Initialize ultrasonic sensor
    sensor = UltrasonicSensor(trig_pin=5, echo_pin=6)

    logger.info("System initialized successfully!")

    # Display ready message
    lcd.clear()
    lcd.write(0, 0, "[READY]")
    lcd.write(0, 1, "System Ready!")
    time.sleep(1)

    try:
        while True:
            # Get distance measurement
            distance = sensor.get_distance()

            logger.info("Distance: %.2f cm", distance)
            lcd.clear()
            lcd.write(0, 0, "[MEASURE]")

            if distance >= 0:
                lcd.write(0, 1, f"Dist: {distance:.1f} cm")
            else:
                lcd.write(0, 1, "Reading Error")

            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Shutting down system...")
        lcd.clear()
        lcd.write(0, 0, "[SHUTDOWN]")
        lcd.write(0, 1, "Goodbye!")
        time.sleep(1)
    except Exception:
        logger.exception("Unexpected error occurred!")
        lcd.clear()
        lcd.write(0, 0, "[ERROR]")
        lcd.write(0, 1, "Check logs!")
        time.sleep(2)
    finally:
        logger.info("Cleaning up resources...")
        lcd.clear()
        lcd.set_backlight(False)
        lcd.cleanup()
        sensor.cleanup()
        GPIO.cleanup()
        logger.info("System shutdown complete!")
