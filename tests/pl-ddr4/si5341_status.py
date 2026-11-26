"""Read Si5341 clock status using PS MIO24/25 and mux channel 1."""
import argparse
from pathlib import Path
from time import monotonic, sleep

SCL, SDA = 24, 25
MUX, CLOCK = 0x70, 0x76


class I2c:
    def __init__(self, pins, active, inactive):
        self.pins, self.high, self.low = pins, active, inactive

    def level(self, pin, high):
        self.pins.set_value(pin, self.high if high else self.low)
        sleep(0.000005)
        if pin == SCL and high:
            end = monotonic() + 0.05
            while self.pins.get_value(SCL) != self.high:
                if monotonic() >= end:
                    raise TimeoutError("SCL stayed low")
                sleep(0.000005)

    def start(self):
        self.level(SDA, True)
        self.level(SCL, True)
        self.level(SDA, False)
        self.level(SCL, False)

    def stop(self):
        self.level(SDA, False)
        self.level(SCL, True)
        self.level(SDA, True)

    def write_byte(self, value):
        for shift in range(7, -1, -1):
            self.level(SDA, bool(value & (1 << shift)))
            self.level(SCL, True)
            self.level(SCL, False)
        self.level(SDA, True)
        self.level(SCL, True)
        accepted = self.pins.get_value(SDA) == self.low
        self.level(SCL, False)
        if not accepted:
            raise OSError(f"I2C NACK for byte {value:#04x}")

    def read_byte(self):
        self.level(SDA, True)
        value = 0
        for _ in range(8):
            self.level(SCL, True)
            value = (value << 1) | (self.pins.get_value(SDA) == self.high)
            self.level(SCL, False)
        self.level(SCL, True)  # NACK the last (only) byte.
        self.level(SCL, False)
        return value

    def write(self, address, *values):
        self.start()
        try:
            self.write_byte(address << 1)
            for value in values:
                self.write_byte(value)
        finally:
            self.stop()

    def read(self, address, register=None):
        self.start()
        try:
            if register is not None:
                self.write_byte(address << 1)
                self.write_byte(register)
                self.start()
            self.write_byte((address << 1) | 1)
            return self.read_byte()
        finally:
            self.stop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    import gpiod
    from gpiod.line import Direction, Drive, Value

    chips = [p for p in Path("/sys/bus/gpio/devices").glob("gpiochip*")
             if "ff0a0000.gpio" in p.resolve().parts]
    if len(chips) != 1:
        raise RuntimeError("cannot identify the PS GPIO controller")
    settings = gpiod.LineSettings(direction=Direction.OUTPUT, drive=Drive.OPEN_DRAIN,
                                  output_value=Value.ACTIVE)
    with gpiod.request_lines(f"/dev/{chips[0].name}", consumer="hamgeek-si5341",
                             config={(SCL, SDA): settings}) as pins:
        bus = I2c(pins, Value.ACTIVE, Value.INACTIVE)
        prev_mux = bus.read(MUX)
        bus.write(MUX, 0x02)
        try:
            deadline = monotonic() + 4
            while bus.read(CLOCK, 0xFE) != 0x0F:
                if monotonic() >= deadline:
                    raise TimeoutError("Si5341 DEVICE_READY is low")
                sleep(0.05)
            prev_page = bus.read(CLOCK, 0x01)
            try:
                bus.write(CLOCK, 0x01, 0)
                identity = [bus.read(CLOCK, reg) for reg in (0x02, 0x03, 0x04, 0x05)]
                status = [bus.read(CLOCK, reg) for reg in (0x0C, 0x0D, 0x0E)]
                print("Si5341 identity:", bytes(identity).hex(" "), "status:", bytes(status).hex(" "))
                if status[0] & 0x1F:
                    raise RuntimeError("Si5341 calibration, reference or PLL status is active")
            finally:
                bus.write(CLOCK, 0x01, prev_page)
        finally:
            bus.write(MUX, prev_mux)


if __name__ == "__main__":
    main()
