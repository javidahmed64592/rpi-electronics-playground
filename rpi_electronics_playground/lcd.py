"""LCD1602 display control module for I2C interface."""

import time

import smbus2 as smbus

from rpi_electronics_playground.base_component import BaseElectronicsComponent


class LCD1602(BaseElectronicsComponent):
    """Class for controlling an LCD1602 display via I2C interface."""

    def __init__(self, address: int = 0x27, backlight: bool = True, bus_number: int = 1) -> None:
        """Initialize the LCD1602 display.

        :param int address: I2C address of the LCD display.
        :param bool backlight: Whether to enable the backlight.
        :param int bus_number: I2C bus number.
        """
        self.address = address
        self.backlight_enabled = backlight
        self.bus_number = bus_number
        self.bus: smbus.SMBus | None = None

        super().__init__("LCD1602")

    def _initialize_component(self) -> None:
        """Initialize the LCD1602 display hardware."""
        self.bus = smbus.SMBus(self.bus_number)
        self._initialize_display()

    def _write_word(self, data: int) -> None:
        """Write a byte to the LCD display.

        :param int data: The byte to write.
        """
        temp = data
        if self.backlight_enabled:
            temp |= 0x08
        else:
            temp &= 0xF7
        self.bus.write_byte(self.address, temp)  # type: ignore[union-attr]

    def _send_command(self, command: int) -> None:
        """Send a command to the LCD display.

        :param int command: The command byte to send.
        """
        # Send bit7-4 firstly
        buf = command & 0xF0
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self._write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self._write_word(buf)

        # Send bit3-0 secondly
        buf = (command & 0x0F) << 4
        buf |= 0x04  # RS = 0, RW = 0, EN = 1
        self._write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self._write_word(buf)

    def _send_data(self, data: int) -> None:
        """Send data to the LCD display.

        :param int data: The data byte to send.
        """
        # Send bit7-4 firstly
        buf = data & 0xF0
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self._write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self._write_word(buf)

        # Send bit3-0 secondly
        buf = (data & 0x0F) << 4
        buf |= 0x05  # RS = 1, RW = 0, EN = 1
        self._write_word(buf)
        time.sleep(0.002)
        buf &= 0xFB  # Make EN = 0
        self._write_word(buf)

    def _initialize_display(self) -> None:
        """Initialize the LCD display with proper settings."""
        try:
            self._send_command(0x33)  # Must initialize to 8-line mode at first
            time.sleep(0.005)
            self._send_command(0x32)  # Then initialize to 4-line mode
            time.sleep(0.005)
            self._send_command(0x28)  # 2 Lines & 5*7 dots
            time.sleep(0.005)
            self._send_command(0x0C)  # Enable display without cursor
            time.sleep(0.005)
            self._send_command(0x01)  # Clear Screen
            self.bus.write_byte(self.address, 0x08)  # type: ignore[union-attr]
            self.logger.info("LCD1602 display initialized successfully at address 0x%02X", self.address)
        except Exception:
            self.logger.exception("Failed to initialize LCD1602 display!")
            raise

    def clear(self) -> None:
        """Clear the LCD display."""
        try:
            self._send_command(0x01)
        except Exception:
            self.logger.exception("Error clearing LCD display!")

    def write(self, x: int, y: int, text: str) -> None:
        """Write text to the LCD display at the specified position.

        :param int x: Column position (0-15).
        :param int y: Row position (0-1).
        :param str text: Text to display.
        """
        # Constrain coordinates to valid ranges
        x = max(0, min(15, x))
        y = max(0, min(1, y))

        # Move cursor to position
        address = 0x80 + 0x40 * y + x
        self._send_command(address)

        # Write each character
        try:
            for char in text:
                self._send_data(ord(char))
        except Exception:
            self.logger.exception("Error writing text to LCD display!")

    def set_backlight(self, enabled: bool) -> None:
        """Enable or disable the LCD backlight.

        :param bool enabled: True to enable backlight, False to disable.
        """
        self.backlight_enabled = enabled
        if enabled:
            self.bus.write_byte(self.address, 0x08)  # type: ignore[union-attr]
        else:
            self.bus.write_byte(self.address, 0x00)  # type: ignore[union-attr]

    def _cleanup_component(self) -> None:
        """Clean up I2C bus resources."""
        try:
            self.set_backlight(False)
            if self.bus:
                self.bus.close()
                self.bus = None
            self.logger.info("LCD1602 cleanup complete.")
        except Exception:
            self.logger.exception("Error during LCD cleanup!")

    def cleanup(self) -> None:
        """Clean up I2C bus resources."""
        self._cleanup_component()


def debug() -> None:
    """Demonstrate LCD1602 functionality."""
    with LCD1602(address=0x27, backlight=True) as lcd:
        try:
            lcd.logger.info("Writing text to LCD...")
            lcd.clear()
            lcd.write(4, 0, "Hello")
            lcd.write(7, 1, "world!")

            time.sleep(3)

            lcd.logger.info("Testing backlight toggle...")
            lcd.set_backlight(False)
            time.sleep(1)
            lcd.set_backlight(True)

            lcd.logger.info("Clearing display...")
            time.sleep(2)
            lcd.clear()

            lcd.logger.info("Demo complete!")

        except KeyboardInterrupt:
            lcd.logger.info("Exiting...")
