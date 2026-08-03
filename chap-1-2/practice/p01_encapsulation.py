
class TemperatureSensor:
    def __init__(self):
        self._temp_readings_celsius = []

    def record(self, celsius: float):
        if celsius < -273.15:
            raise ValueError("Temperature below absolute zero")
        
        self._temp_readings_celsius.append(celsius)

    @property
    def latest(self):
        return self._temp_readings_celsius[-1]

    @property
    def average(self):
        return sum(self._temp_readings_celsius) / len(self._temp_readings_celsius)


temperature_sensor = TemperatureSensor()

temperature_sensor.record(98.4)
temperature_sensor.record(99.3)
temperature_sensor.record(-57.2)

latest_reading = temperature_sensor.latest
average = temperature_sensor.average

print(f"Latest reading: {latest_reading}.")
print(f"Average reading: {average}")
