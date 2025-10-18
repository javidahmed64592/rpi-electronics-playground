"""RFID reader/writer module for MFRC522."""

import logging
import time

from mfrc522 import SimpleMFRC522
from RPi import GPIO

logging.basicConfig(format="%(asctime)s %(message)s", datefmt="[%d-%m-%Y|%H:%M:%S]", level=logging.INFO)
logger = logging.getLogger(__name__)


class RFIDReader:
    """Class for handling RFID operations using MFRC522."""

    def __init__(self) -> None:
        """Initialize the RFID reader."""
        self.reader = SimpleMFRC522()

    def read_card(self) -> tuple[int, str] | None:
        """Read data from an RFID card.

        :return: Tuple of (card_id, text) if card is detected, None otherwise.
        """
        try:
            return self.reader.read()  # type: ignore[no-any-return]
        except Exception:
            logger.exception("Error reading card!")
            return None

    def write_card(self, text: str) -> bool:
        """Write data to an RFID card.

        :param str text: The text to write to the card.
        :return: True if write successful, False otherwise.
        """
        try:
            self.reader.write(text)
        except Exception:
            logger.exception("Error writing to card!")
            return False
        else:
            return True


def debug() -> None:
    """Debug function to test RFID reader/writer functionality."""
    rfid = RFIDReader()

    try:
        while True:
            logger.info("Place an RFID card near the reader...")
            result = rfid.read_card()
            if result:
                card_id, text = result
                logger.info("Read from card - ID: %s, Text: %s", card_id, text.strip())

                new_text = str(input("Enter new text to write to the card: "))
                if rfid.write_card(new_text):
                    logger.info("Wrote to card - New Text: %s", new_text)
            time.sleep(2)
    except KeyboardInterrupt:
        logger.info("Exiting RFID debug mode.")
    finally:
        GPIO.cleanup()
