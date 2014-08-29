# Copyright (C) 2014-2014 Project
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher

import argparse
import logging

_logger = logging.getLogger('pwebs.main')
#logging.basicConfig(level=0)

exitcodes = {'OK': 0,
             'Warning': 1,
             'Critical': 2,
             'Unknown': 3}


def _get_threshold_range(data):
    import re
    _logger.debug('Got the folowing data for _get_threshold_range: %s' % data)
    if ':' in data:
        value_strings = data.split(':')
        match0 = re.match('([~]|[0-9]+)$', value_strings[0])
        match1 = re.match('[0-9]+$', value_strings[1])
        if not (match0 and match1):
            raise argparse.ArgumentTypeError('Supplied range contains invalid character(s)')
        value1 = int(value_strings[1])
        if value_strings[0] == '~':
            value0 = value_strings[0]
        else:
            value0 = int(value_strings[0])
            if value0 > value1:
                raise argparse.ArgumentTypeError('Invalid range; lower bound must be smaller than upper bound')
        values = (value0, value1)
    else:
        match = re.match('[0-9]+$', data)
        if not match:
            raise argparse.ArgumentTypeError('Supplied Argument contains invalid character(s)')
        values = (0, int(data))
    return values


def threshold(data):
    _logger.debug('threshold testing data: %s' % data)
    import re
    re_in = 'i(?:n)?([^,]+)'
    re_out = 'o(?:ut)?([^,]+)'
    l_in = re.findall(re_in, data)
    l_out = re.findall(re_out, data)
    if not (l_in or l_out):
        range_in = _get_threshold_range(data)
        range_out = range_in
    elif not l_in:
        range_in = None
        range_out = _get_threshold_range(l_out[0])
    elif not l_out:
        range_out = None
        range_in = _get_threshold_range(l_in[0])
    else:
        range_in = _get_threshold_range(l_in[0])
        range_out = _get_threshold_range(l_out[0])
    return (range_in, range_out)


def run():
    nagios_base_parser = argparse.ArgumentParser(add_help=False)
    nagios_base_parser.add_argument('-H', '--hostname', required=True,
                                    help='The Host to check')
    nagios_base_parser.add_argument('-v', action='count', default=0)
    nagios_parser = argparse.ArgumentParser(add_help=False,
                                            parents=[nagios_base_parser])
    nagios_parser.add_argument('-c', '--critical', required=True,
                               type=threshold,
                               help='The lower bound for CRITICAL Error, or non-CRITICAL range')
    nagios_parser.add_argument('-w', '--warning', required=True,
                               type=threshold,
                               help='The lower bound for WARNING Error, or non-WARNING range')

    parser = argparse.ArgumentParser(
        description='FIXME some fancy description here')
    subparsers = parser.add_subparsers()

    parser_rittal = subparsers.add_parser('rittal',
                                          help='Check a cabinet of type rittal',
                                          parents=[nagios_parser])
    parser_rittal.add_argument('category', choices=['Water', 'Air',
                                                    'CoolingCapacity'])
    parser_rittal.add_argument('--select', choices=['in', 'out', 'both'],
                               default='both')
    parser_rittal.add_argument('-u', '--user', required=True,
                               help='The user to login with')
    parser_rittal.add_argument('-p', '--password', required=True,
                               help='The password to login with')
    parser_rittal.set_defaults(func=_parse_rittal)

    args = parser.parse_args()
    logging.basicConfig(level=50 - (args.v * 10))
    try:
        exitcode, text = args.func(args)
    except Exception as e:
        exitcode = exitcodes.get('Unknown', 3)
        text = str(e)
        _logger.exception('Caught an Exception! What happened?')
    print(text)
    exit(exitcode)


def _parse_rittal(args):
    from .rittal import Rittal
    hostname = args.hostname
    critical = args.critical
    warning = args.warning
    category = args.category
    category_extra = args.select
    user = args.user
    password = args.password
    cabinet = Rittal(hostname, user, password)
    water_in = cabinet.water_in
    water_out = cabinet.water_out
    air_in = cabinet.air_in
    air_out = cabinet.air_out
    #setpoint = cabinet.setpoint # don't know, seems not important
    cooling_capacity = cabinet.cooling_capacity
    waterflow = cabinet.waterflow
    control_valve = cabinet.control_valve

    text = ''
    exitcode = 3
    if category == 'Water':
        labels = _create_labels('Water', category_extra)
        exitcode, text = _check_temperatures(hostname, labels, water_in,
                                             water_out, warning, critical,
                                             {'Waterflow': waterflow,
                                              'Control Valve': control_valve})
    elif category == 'Air':
        labels = _create_labels('Air', category_extra)
        exitcode, text = _check_temperatures(hostname, labels, air_in, air_out,
                                             warning, critical)
    elif category == 'CoolingCapacity':
        text = _get_text_ok(hostname, 'Cooling Capacity', cooling_capacity,
                            None, None, None)
        exitcode = exitcodes.get('OK', 3)
    return exitcode, text


def _create_labels(category, category_extra):
    import re
    labels = []
    if re.match('(in|both)', category_extra):
        labels.append(category + ' in')
    if re.match('(out|both)', category_extra):
        labels.append(category + ' out')
    return labels


def _check_temperatures(hostname, labels, value_in, value_out, warning,
                        critical, extra=None):
    if _values_ok(value_in, value_out, *critical):
        if _values_ok(value_in, value_out, *warning):
            get_text = _get_text_ok
            exitcode = exitcodes.get('OK', 3)
        else:
            get_text = _get_text_warning
            exitcode = exitcodes.get('Warning', 3)
    else:
        get_text = _get_text_critical
        exitcode = exitcodes.get('Critical', 3)
    text = get_text(hostname, labels, value_in, value_out, warning, critical,
                    extra)
    return exitcode, text


def _values_ok(value_in, value_out, threshold_in, threshold_out):
    _logger.debug('Checking values. In: %s, out: %s' % (threshold_in,
                                                        threshold_out))
    in_ok = True
    out_ok = True
    if threshold_in:
        in_ok = _is_in_range(int(value_in[0]), *threshold_in)
    if threshold_out:
        out_ok = _is_in_range(int(value_out[0]), *threshold_out)
    return (in_ok and out_ok)


def _is_in_range(value, lower_bound, upper_bound):
    is_in_range = True
    if lower_bound != '~':
        is_in_range = value >= lower_bound
    is_in_range = is_in_range and value <= upper_bound
    return is_in_range


def _get_text_warning(hostname, labels, temperature_in, temperature_out,
                      warning, critical, extra=None):
    return 'Warning' + _get_text(hostname, labels, temperature_in,
                                 temperature_out, warning, critical, extra)


def _get_text_critical(hostname, labels, temperature_in, temperature_out,
                       warning, critical, extra=None):
    return 'Critical' + _get_text(hostname, labels, temperature_in,
                                  temperature_out, warning, critical, extra)


def _get_text_ok(hostname, labels, temperature_in, temperature_out,
                 warning, critical, extra=None):
    return 'OK' + _get_text(hostname, labels, temperature_in,
                            temperature_out, warning, critical, extra)


def _get_text(hostname, labels, temperature_in, temperature_out,
              warning, critical, extra=None):
    if not warning:
        warning = [[], []]
    if not critical:
        critical = [[], []]
    text = ' - %s %s%s' % (labels[0], temperature_in[0], temperature_in[1])
    if temperature_out:
        text += ' %s: %s%s' % (labels[1], temperature_out[0],
                               temperature_out[1])
    text += '| '
    text += _get_pnp_text(labels, temperature_in, temperature_out, warning,
                          critical, extra)
    return text


def _get_pnp_text(labels, temperature_in, temperature_out, warning, critical,
                  extra=None):
    value, uom = temperature_in  # uom = Unit of Measurement; etwa Celsius, etc.
    text = _format_label(labels[0], value, uom, warning[0], critical[0])
    if temperature_out:
        text += ' '
        value, uom = temperature_out  # uom = Unit of Measurement; etwa Celsius, etc.
        text += _format_label(labels[1], value, uom, warning[1], critical[1])
    if extra:
        for key, value in extra.items():
            text += ' ' + _format_label(key, ''.join(value), '')
    return text


def _format_label(label, value, uom, warning=None, critical=None):
    # uom = Unit of Measurement; Maßeinheit, etwa Celsius, etc.
    text = "'%s'=%s%s;" % (label, value, uom)
    if warning:
        text += '%s:%s' % warning
    text += ';'
    if critical:
        text += '%s:%s' % critical
    text += ';;'
    return text
