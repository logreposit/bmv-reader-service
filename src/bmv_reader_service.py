#!/usr/bin/env python3

import calendar
import datetime
import json
import os
import sys
import time
import requests

from bmv_reader import BMVReader
from bmv_reader import BMVReaderError
from bmv_reading import BMVReading


SERIAL_DEVICE_ENV_VAR_NAME = 'SERIAL_DEVICE'
API_BASE_URL_ENV_VAR_NAME = 'API_BASE_URL'
DEVICE_TOKEN_ENV_VAR_NAME = 'DEVICE_TOKEN'
BMV_MODEL_ENV_VAR_NAME = 'BMV_MODEL'
FETCH_INTERVAL_ENV_VAR_NAME = 'FETCH_INTERVAL'

SERIAL_DEVICE_DEFAULT_VALUE = '/dev/ttyUSB0'
API_BASE_URL_DEFAULT_VALUE = 'https://api.logreposit.com/v1/'
FETCH_INTERVAL_DEFAULT_VALUE = 5


def _get_utc_timestamp():
    return calendar.timegm(datetime.datetime.utcnow().utctimetuple())


def _check_required_environment_variables():
    bmv_model = os.getenv(BMV_MODEL_ENV_VAR_NAME, None)
    device_token = os.getenv(DEVICE_TOKEN_ENV_VAR_NAME, None)

    if bmv_model is None:
        print('ERROR: you have to specify the bmv model in the env var \'{}\'!'.format(BMV_MODEL_ENV_VAR_NAME))
        sys.exit(1)

    if device_token is None:
        print('Error: you have to specify a logreposit device-token in the env var \'{}\'!'
              .format(DEVICE_TOKEN_ENV_VAR_NAME))
        sys.exit(2)


def _validate_bmv_model(bmv_model):
    if bmv_model not in [600, 602]:
        print('ERROR: only supported bmv models are 600 and 602')
        sys.exit(3)


def _sleep_interval(interval):
    print('Sleeping {} seconds'.format(interval))
    time.sleep(interval)


def _convert_on_off_boolean(state):
    if state == 'ON':
        return True
    if state == 'OFF':
        return False
    return False


def _prepare_data_for_publishing(bmv_reading: BMVReading):
    state_of_charge = bmv_reading.state_of_charge
    if state_of_charge is not None:
        state_of_charge = state_of_charge * 0.1

    alarm = _convert_on_off_boolean(state=bmv_reading.alarm)
    relay = _convert_on_off_boolean(state=bmv_reading.relay)

    data = {
        'date': _get_utc_timestamp(),
        'stateOfCharge': state_of_charge,
        'alarm': alarm,
        'relay': relay,
        'batteryVoltage': bmv_reading.battery_voltage,
        'starterBatteryVoltage': bmv_reading.starter_battery_voltage,
        'current': bmv_reading.current,
        'consumedEnergy': bmv_reading.consumed_energy,
        'timeToGo': bmv_reading.time_to_go
    }

    return data


def _build_request_data(bmv_reading: BMVReading):
    bmv_data = _prepare_data_for_publishing(bmv_reading=bmv_reading)

    data = {
        'deviceType': 'VICTRON_ENERGY_BMV600',
        'data': bmv_data
    }

    return data


def _publish_values(bmv_reading, api_base_url, device_token):
    url = api_base_url + 'ingress'
    headers = {
        'x-device-token': device_token
    }
    request_data = _build_request_data(bmv_reading=bmv_reading)

    print('Publishing values: {}'.format(json.dumps(request_data)))
    response = requests.post(url, json=request_data, headers=headers)

    if response.status_code != 202:
        print('ERROR: Got HTTP status code \'{}\': {}'.format(response.status_code, response.raw))
    else:
        print('Successfully published data.')


def _read_and_publish_values(serial_device, bmv_model, api_base_url, device_token):
    bmv_reader = BMVReader(serial_port=serial_device, model=bmv_model)

    print('Reading values from BMV ...')
    bmv_reading = bmv_reader.get_reading()

    _publish_values(bmv_reading=bmv_reading, api_base_url=api_base_url, device_token=device_token)


def main():
    _check_required_environment_variables()

    bmv_model = os.getenv(BMV_MODEL_ENV_VAR_NAME)
    device_token = os.getenv(DEVICE_TOKEN_ENV_VAR_NAME)
    serial_device = os.getenv(SERIAL_DEVICE_ENV_VAR_NAME, SERIAL_DEVICE_DEFAULT_VALUE)
    api_base_url = os.getenv(API_BASE_URL_ENV_VAR_NAME, API_BASE_URL_DEFAULT_VALUE)
    fetch_interval = os.getenv(FETCH_INTERVAL_ENV_VAR_NAME, FETCH_INTERVAL_DEFAULT_VALUE)

    while True:
        _sleep_interval(interval=fetch_interval)

        try:
            _read_and_publish_values(serial_device=serial_device,
                                     bmv_model=bmv_model,
                                     api_base_url=api_base_url,
                                     device_token=device_token)
        except BMVReaderError as e:
            print('ERROR: Caught BMVReaderError: {}'.format(type(e)))
        except Exception as e:
            print('ERROR: Caught Exception', e)


if __name__ == '__main__':
    main()
