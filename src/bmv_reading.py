class BMVReading:
    def __init__(self, battery_voltage, starter_battery_voltage, current, consumed_energy, state_of_charge, time_to_go,
                 alarm, relay):
        self.battery_voltage = battery_voltage
        self.starter_battery_voltage = starter_battery_voltage
        self.current = current
        self.consumed_energy = consumed_energy
        self.state_of_charge = state_of_charge
        self.time_to_go = time_to_go
        self.alarm = alarm
        self.relay = relay
