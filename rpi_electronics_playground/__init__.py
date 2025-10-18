"""Raspberry Pi Electronics Playground Library

A modular library for interfacing with various electronic components on Raspberry Pi.
This library provides standardized classes for common electronic components, with
built-in logging, error handling, and context manager support for automatic cleanup.

Components:
- RFIDReader: MFRC522 RFID card reader/writer
- ServoMotor: Servo motor control with lock/unlock functionality
- StepperMotor: 28BYJ-48 stepper motor with ULN2003 driver
- UltrasonicSensor: HC-SR04 ultrasonic distance sensor with filtering
- LCD1602: LCD1602 I2C display controller

Usage:
    from rpi_electronics_playground import RFIDReader, ServoMotor

    # Use components with context managers for automatic cleanup
    with RFIDReader() as rfid:
        card_id = rfid.read_card()

    with ServoMotor(servo_pin=18) as servo:
        servo.unlock()
"""

from .base_component import BaseElectronicsComponent
from .rfid_reader import RFIDReader
from .servo_motor import ServoMotor
from .stepper_motor import StepperMotor
from .ultrasonic_sensor import UltrasonicSensor
from .lcd import LCD1602

# Define what gets imported with "from rpi_electronics_playground import *"
__all__ = [
    "BaseElectronicsComponent",
    "RFIDReader",
    "ServoMotor",
    "StepperMotor",
    "UltrasonicSensor",
    "LCD1602",
]
