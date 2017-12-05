from operator import attrgetter
import time

import pigpio
from pigpio import OUTPUT

from puddle.arch import Architecture

# HV507 polarity
# Pin 32 - BCM 12 (PWM0)
POLARITY_PIN = 12

# High voltage converter "analog" signal
# Pin 33 - BCM 13 (PWM1)
VOLTAGE_PIN = 13

# HV507 blank
# Pin 11 - BCM 17
BLANK_PIN = 17

# TODO fix pin numbers

# HV507 latch enable
# Pin 27 - BCM 13
LATCH_ENABLE_PIN = 13

# HV507 clock
# Pin 22 - BCM 15
CLOCK_PIN = None

# HV507 data
# Pin 23 - BCM 16
DATA_PIN = None

# full duty cycle according to pigpio
FULL_DUTY = 1000000

# delay between steps in seconds
STEP_DELAY = 1


class PurpleDrop(Architecture):

    def __init__(self, graph):
        super().__init__(graph)

        # cells sorted by id
        # we write out the data to the serial port in order of id
        self.sorted_cells = sorted(
            self.cells(),
            key=attrgetter('id')
        )

        self.pi = pigpio.pi()

    def setup_pins(self):

        pi = self.pi

        pi.hardware_PWM(
            gpio = POLARITY_PIN,
            PWMfreq = 490,    # same freq as arduino's analogWrite
            PWMduty = FULL_DUTY / 2, # half duty cycle
        )

        target_voltage = 140
        chip_out_voltage = 5   # we go through 3.3v -> 5v buffer first
        hv_in_voltage = 2.048
        hv_out_voltage = 500

        assert target_voltage < hv_out_voltage

        hv_frac = target_voltage / hv_out_voltage
        chip_frac = hv_in_voltage / chip_out_voltage

        assert 0 < hv_frac < 1
        assert 0 < chip_frac < 1

        hv_duty = FULL_DUTY * hv_frac * chip_frac

        pi.hardware_PWM(
            gpio = VOLTAGE_PIN,
            PWMfreq = 100000, # higher freq, this is an "analog" signal
            PWMduty = hv_duty,
        )

        # setup the HV507 for serial data write
        # see row "LOAD S/R" in table 3-2 in
        # http://ww1.microchip.com/downloads/en/DeviceDoc/20005845A.pdf

        pi.set_mode(BLANK_PIN, OUTPUT)
        pi.write(BLANK_PIN, 1)

        pi.set_mode(LATCH_ENABLE_PIN, OUTPUT)
        pi.write(LATCH_ENABLE_PIN, 0)

        pi.set_mode(CLOCK_PIN, OUTPUT)
        pi.write(CLOCK_PIN, 0)

        pi.set_mode(DATA_PIN, OUTPUT)
        pi.write(DATA_PIN, 0)

    def wait(self):

        pi = self.pi

        active_cells = set.union(
            drop.locations
            for drop in self.droplets
        )

        for cell in self.sorted_cells():
            is_active = 1 if cell in active_cells else 0
            pi.write(DATA_PIN, is_active)

            # cycle clock to actually write
            pi.write(CLOCK_PIN, 1)
            pi.write(CLOCK_PIN, 0)

        # commit the latch
        pi.write(LATCH_ENABLE_PIN, 1)
        pi.write(LATCH_ENABLE_PIN, 0)

        super().wait()

        time.sleep(STEP_DELAY)


if __name__ == '__main__':
    arch = PurpleDrop.from_file('tests/arches/purpledrop.yaml')
