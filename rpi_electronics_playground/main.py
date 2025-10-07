"""Main application for the Raspberry Pi Electronics Playground."""

import logging
import time

from RPi import GPIO

from rpi_electronics_playground.lcd import LCD1602

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


def run() -> None:
    """Run the Raspberry Pi Electronics Playground."""
    logger.info("Initializing Raspberry Pi Electronics Playground...")

    # Initialize LCD display
    lcd = LCD1602(address=0x27, backlight=True)
    lcd.clear()
    lcd.write(0, 0, "Electronics Playground")
    lcd.write(0, 1, "Initializing...")

    logger.info("System initialized successfully!")

    # Display ready message
    lcd.clear()
    lcd.write(0, 0, "Electronics Playground")
    lcd.write(0, 1, "Ready!")

    try:
        index = 0
        while True:
            logger.info("Timestep: %d", index)
            lcd.clear()
            lcd.write(0, 0, "Electronics Playground")
            lcd.write(0, 1, f"Timestep: {index}")
            index += 1
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down system...")
        lcd.clear()
        lcd.write(0, 0, "Shutting Down")
        lcd.write(0, 1, "Goodbye!")
        time.sleep(1)
    except Exception:
        logger.exception("Unexpected error occurred!")
        lcd.clear()
        lcd.write(0, 0, "System Error")
        lcd.write(0, 1, "Check logs!")
        time.sleep(2)
    finally:
        logger.info("Cleaning up resources...")
        lcd.clear()
        lcd.set_backlight(False)
        lcd.cleanup()
        GPIO.cleanup()
        logger.info("System shutdown complete!")
