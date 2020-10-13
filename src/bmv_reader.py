#!/usr/bin/env python3

import json
import serial

from bmv_reading import BMVReading

CHECKSUM_VALUE_NAME = 'Checksum'

BMV_600_VALUE_NAMES = ['V', 'I', 'CE', 'SOC', 'TTG', 'Alarm', 'Relay', 'AR', 'BMV', 'FW', CHECKSUM_VALUE_NAME, 'H1',
                       'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12', CHECKSUM_VALUE_NAME]

BMV_602_VALUE_NAMES = ['V', 'VS0', 'I', 'CE', 'SOC', 'TTG', 'Alarm', 'Relay', 'AR', 'BMV', 'FW', CHECKSUM_VALUE_NAME,
                       'H1','H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12', 'H13', 'H14', 'H15',
                       'H16', CHECKSUM_VALUE_NAME]

NON_INTEGER_VALUE_NAMES = ['Alarm', 'Relay', 'BMV', 'AR', 'FW', CHECKSUM_VALUE_NAME]


class BMVReaderError(Exception):
    pass


class ChecksumError(BMVReaderError):
    pass


class NoDataError(BMVReaderError):
    pass


class BMVReader:

    def __init__(self, serial_port, model):
        self._setup_device_settings(model=model)
        self.serial = serial.Serial(serial_port, 19200, timeout=1)

    def _setup_device_settings(self, model):
        if model == 602:
            self.value_names = BMV_602_VALUE_NAMES
            self.line_count_limit = [29, 11, 28]
        else:
            self.value_names = BMV_600_VALUE_NAMES
            self.line_count_limit = [24, 10, 23]

    def _read_values(self):
        line_count = 0
        last_byte = b''
        current_byte = b''
        put_value = False

        self.serial.flushInput()

        for i in range(0, 400):
            values = []
            value = b''

            if last_byte == b'\n' and current_byte == b'V':
                integer_value = ord('\r') + ord(last_byte)

                while line_count < self.line_count_limit[0]:

                    if line_count == self.line_count_limit[1] and current_byte == b'\r':
                        self._validate_checksum(checksum=integer_value)
                        integer_value = 0  # reset for round 2

                    elif line_count == self.line_count_limit[2] and current_byte == b'\r':
                        self._validate_checksum(checksum=integer_value)

                    integer_value += ord(current_byte)

                    if last_byte == b'\t':
                        put_value = True

                    if put_value and current_byte != b'\r' and current_byte != b'\n':
                        value = value + current_byte

                    if current_byte == b'\n':
                        values.append(value)
                        line_count += 1
                        value = b''
                        put_value = False

                    last_byte, current_byte = self._read_byte_from_serial(current_byte)

            if line_count == 0:
                last_byte, current_byte = self._read_byte_from_serial(current_byte)

            else:
                return values

        raise NoDataError()

    def _read_byte_from_serial(self, current_byte):
        result = self.serial.read(1)
        return current_byte, result

    @staticmethod
    def _validate_checksum(checksum):
        if (checksum % 256) is not 0:
            raise ChecksumError()

    def _convert_to_dictionary(self, values):
        data = {}

        for value_name in self.value_names:
            if value_name is CHECKSUM_VALUE_NAME:
                continue

            index = self.value_names.index(value_name)
            value = values[index].decode('utf-8')

            if value == '---':
                value = None
            elif value_name not in NON_INTEGER_VALUE_NAMES:
                value = int(value)

            data[value_name] = value

        return data

    def read(self):
        values = self._read_values()
        return self._convert_to_dictionary(values=values)

    def get_reading(self):
        values = self.read()

        battery_voltage = values.get('V')
        starter_battery_voltage = values.get('VS0')
        current = values.get('I')
        consumed_energy = values.get('CE')
        state_of_charge = values.get('SOC')
        time_to_go = values.get('TTG')
        alarm = values.get('Alarm')
        relay = values.get('Relay')

        bmv_reading = BMVReading(battery_voltage=battery_voltage,
                                 starter_battery_voltage=starter_battery_voltage,
                                 current=current,
                                 consumed_energy=consumed_energy,
                                 state_of_charge=state_of_charge,
                                 time_to_go=time_to_go,
                                 alarm=alarm,
                                 relay=relay)

        return bmv_reading


def main():
    bmv_reader = BMVReader(serial_port='/dev/ttyUSB0', model=600)
    data = bmv_reader.read()
    json_representation = json.dumps(data)
    print(json_representation)


if __name__ == '__main__':
    main()

