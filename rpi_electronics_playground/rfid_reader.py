"""RFID reader/writer module for MFRC522."""

import time

from mfrc522 import SimpleMFRC522

from rpi_electronics_playground.base_component import BaseElectronicsComponent


class RFIDReader(BaseElectronicsComponent):
    """Class for handling RFID operations using MFRC522."""

    def __init__(self) -> None:
        """Initialize the RFID reader."""
        super().__init__("RFIDReader")

    def _initialize_component(self) -> None:
        """Initialize the RFID reader hardware."""
        self.reader = SimpleMFRC522()

    def read_card(self) -> tuple[int, str] | None:
        """Read data from an RFID card.

        :return: Tuple of (card_id, text) if card is detected, None otherwise.
        """
        try:
            return self.reader.read()  # type: ignore[no-any-return]
        except Exception:
            self.logger.exception("Error reading card!")
            return None

    def write_card(self, text: str) -> bool:
        """Write data to an RFID card.

        :param str text: The text to write to the card.
        :return: True if write successful, False otherwise.
        """
        try:
            self.reader.write(text)
        except Exception:
            self.logger.exception("Error writing to card!")
            return False
        else:
            return True

    def _cleanup_component(self) -> None:
        """Clean up RFID reader resources."""
        # The MFRC522 library doesn't require specific cleanup,
        # but we ensure GPIO cleanup is handled by the base class


def debug() -> None:
    """Debug function to test RFID reader/writer functionality."""
    with RFIDReader() as rfid:
        try:
            while True:
                rfid.logger.info("Place an RFID card near the reader...")
                result = rfid.read_card()
                if result:
                    card_id, text = result
                    rfid.logger.info("Read from card - ID: %s, Text: %s", card_id, text.strip())

                    new_text = str(input("Enter new text to write to the card: "))
                    if rfid.write_card(new_text):
                        rfid.logger.info("Wrote to card - New Text: %s", new_text)
                time.sleep(2)
        except KeyboardInterrupt:
            rfid.logger.info("Exiting RFID debug mode.")
