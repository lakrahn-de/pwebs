# Copyright (C) 2014-2014 Project
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher

import argparse
import logging


class ArgumentTypeError(argparse.ArgumentTypeError):
    pass


class InvalidService(ValueError):
    pass


class NagiosConfig:
    watches = ('water', 'air', 'performance')
    types = ('rittal', )

    command_template = '''
define command {
    command_name    check_$hostname\_$type
    command_line    $install_path/check_ludwig $type $value -H $hostname \
        --warning $warning_temps \
        --critical $critical_temps
}
'''

    service_template = '''
define service {
    host_name       $hostname
    service_description     $type watcher of $hostname
    check_command           $command
    max_check_attempts      x
    check_interval          x
    retry_interval          x
    check_period            x
    notification_interval   x
    notification_period     x
    contacts                x
    contact_groups          x
}
'''

    hostgroup_template = '''
define hostgroup {
    hostgroup_name  $hostname\_$type_clients
    alias           $hostname $type Clients
}
'''

    host_template = '''
define host {
    host_name   $hostname
    alias       $hostname
    address     $hostname
    max_check_attempts  x
    check_attempts      x
    check_period        x
    contacts            x
    contact_groups      x
    notification_interval   x
    notification_period     x
}
'''

    # FIXME this doesn't seem to be right.
    timeperiods = '''
define timeperiod {
    timeperiod_name pwebs_fulltime
    alias           PWebs 24/7
}
'''

    def __init__(self, config):
        self._config = config

    def _hosts(self):
        for section in self._config.sections():
            yield section

    def _services(self):
        for h in self._hosts():
            services = self._config.get(h, 'watch').split(',')
            for s in services:
                s = s.strip()
                if s not in NagiosConfig.watches:
                    raise InvalidService('Got %s as watch in %s' % (s.strip(), h))
                yield (h, s)

    def generate(self):
        raise NotImplementedError()

    def generate_pnp4nagios_cfg(self):
        raise NotImplementedError()


def config(source):
    ''' Converts a string into a SafeConfigParser instance and raises an
    exception if the string is not a valid ini like file.

    Args:
        source (str): path to config file.

    Returns:
        A instance of SafeConfigParser with config file already read.

    Raises:
        argparse.ArgumentError: Input was invalid in some kind.
    '''
    import configparser
    config = configparser.SafeConfigParser()
    argument_error = ArgumentTypeError('Was unable to read configuration '
                                       '%s' % source)
    try:
        read = config.read(source)
        if not read:
            raise argument_error
    except configparser.Error:
        raise argument_error
    return config


def output_file(path):
    ''' File to which the nagios configuration shall be written.

    Args:
        path (str): path to output file or '-' for output to stdout.

    Returns:
        File like object of the output file.

    Raises:
        argparse.ArgumentError: Input was invalid in some kind.
    '''
    import sys
    if path == '-':
        return sys.stdout

    try:
        f = open(path, 'w')
        return f
    except (PermissionError, FileNotFoundError):
        raise ArgumentTypeError('Unable to write to file %s' % path)


def configure():
    desc = 'Nagios configurator. This tool generates the nagios.cfg which can'
    desc += ' be used to bind pwebs to nagios'
    parser = argparse.ArgumentParser(description=desc)

    parser.add_argument('-c', '--config', default='/etc/pwebs/pwebs.ini',
                        type=config,
                        help='The pwebs source file for the nagios configuration'
                        )
    parser.add_argument('output', type=output_file,
                        help='Nagios configuration. If \'-\' is given the '
                        'config will be printed to stdout')
    parser.add_argument('-v', action='count', default=0,
                        help='increase verbosity.')
    args = parser.parse_args()

    logging.basicConfig(level=50 - args.v * 10)
