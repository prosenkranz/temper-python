# encoding: utf-8
from __future__ import print_function, absolute_import
from prometheus_client import start_http_server, Gauge
import argparse
import logging
import time

from .temper import TemperHandler


def parse_args():
    descr = "Temperature data from a TEMPer v1.2/v1.3 sensor."

    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument("-p", "--disp_ports", action='store_true',
                        help="Display ports")
    units = parser.add_mutually_exclusive_group(required=False)
    units.add_argument("-c", "--celsius", action='store_true',
                       help="Quiet: just degrees celcius as decimal")
    units.add_argument("-f", "--fahrenheit", action='store_true',
                       help="Quiet: just degrees fahrenheit as decimal")
    units.add_argument("-H", "--humidity", action='store_true',
                       help="Quiet: just percentage relative humidity as decimal")
    parser.add_argument("-s", "--sensor_ids", choices=['0', '1', 'all'],
                        help="IDs of sensors to use on the device " +
                        "(multisensor devices only)", default='0')
    parser.add_argument("-S", "--sensor_count", type=int,
                        help="Override auto-detected number of sensors on the device")
    parser.add_argument("-v", "--verbose", action='store_true',
                       help="Verbose: display all debug information")
    parser.add_argument("--prometheus-exporter", dest='prometheus_exporter', action='store_true',
                        help="Starts a foreground webserver that servers Prometheus " +
                        "Metrics instead of printing them to console")
    args = parser.parse_args()

    return args


def get_quiet(args):
    return args.celsius or args.fahrenheit or args.humidity


def sample_sensors(args):
    quiet = get_quiet(args)

    th = TemperHandler()
    devs = th.get_devices()
    if not quiet:
        print("Found %i devices" % len(devs))

    readings = []

    for dev in devs:
        if args.sensor_count is not None:
            # Override auto-detection from args
            dev.set_sensor_count(int(args.sensor_count))

        if args.sensor_ids == 'all':
            sensors = range(dev.get_sensor_count())
        else:
            sensors = [int(args.sensor_ids)]

        temperatures = dev.get_temperatures(sensors=sensors)
        humidities = dev.get_humidity(sensors=sensors)
        combinations = {}
        for k, v in temperatures.items():
            c = v.copy()
            try:
                c.update(humidities[k])
            except:
                pass
            combinations[k] = c
        readings.append(combinations)

    return readings


def main_simple(args):
    quiet = get_quiet(args)

    readings = sample_sensors(args)

    for i, reading in enumerate(readings):
        output = ''
        if quiet:
            if args.celsius:
                dict_key = 'temperature_c'
            elif args.fahrenheit:
                dict_key = 'temperature_f'
            elif args.humidity:
                dict_key = 'humidity_pc'

            for sensor in sorted(reading):
                output += '%0.1f; ' % reading[sensor][dict_key]
            output = output[0:len(output) - 2]
        else:
            portinfo = ''
            tempinfo = ''
            huminfo = ''
            for sensor in sorted(reading):
                if args.disp_ports and portinfo == '':
                    portinfo = " (bus %(bus)s - port %(ports)s)" % reading[sensor]
                try:
                    tempinfo += '%0.1f°C %0.1f°F; ' % (
                        reading[sensor]['temperature_c'],
                        reading[sensor]['temperature_f'],
                    )
                except:
                    pass
                try:
                    huminfo += '%0.1f%%RH; ' % (reading[sensor]['humidity_pc'])
                except:
                    pass
            tempinfo = tempinfo[0:len(output) - 2]
            huminfo = huminfo[0:len(output) - 2]

            output = 'Device #%i%s: %s %s' % (i, portinfo, tempinfo, huminfo)
        print(output)


def main_prometheus_exporter(args):
    start_http_server(8000)

    # Register metrics
    temperature_c_gauge = Gauge('temper_temperature_c', 'Temperature in Degrees Celsius', ['device', 'sensor'])
    humidity_pc_gauge = Gauge('temper_humidity_pc', 'Humidity in percent', ['device', 'sensor'])

    while True:
        print("Sampling...")

        readings = sample_sensors(args)

        for i, reading in enumerate(readings):
            for sensor in sorted(reading):
                temperature_c_gauge.labels(device=str(i), sensor=str(sensor)).set(reading[sensor]['temperature_c'])

                try:
                    humidity_pc = reading[sensor]['humidity_pc']
                    humidity_pc_gauge.labels(device=str(i), sensor=str(sensor)).set(humidity_pc)
                except:
                    pass

        time.sleep(10)





def main():
    args = parse_args()
    quiet = get_quiet(args)
    lvl = logging.ERROR if quiet else logging.WARNING
    if args.verbose:
        lvl = logging.DEBUG
    logging.basicConfig(level = lvl)

    if args.prometheus_exporter:
        main_prometheus_exporter(args)
    else:
        main_simple(args)


if __name__ == '__main__':
    main()
