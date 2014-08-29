# Copyright (C) 2014-2014 Project
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher

import unittest
from pwebs import nagios

config = '''
[cabinet_01]
username = foo
password = secret
type = rittal
watch = water, air, performance

water_warning = in20,out25
water_critical = in25,out28

air_warning = in20,out25
air_critical = in25,out28

nodes = dnode001-dnode017,dnode250,192.168.1.11-192.168.1.15,10.8.1.1

[cabinet_02]
username = foo2
password = secret2
type = rittal
watch = water, air

water_warning = in20,out25
water_critical = in23,out28

air_warning = in20,out25
air_critical = in25,out28

nodes = node1-node10,node200

[192.168.1.1]
watch = air
'''


class TestNagiosConfig(unittest.TestCase):
    def setUp(self):
        import random
        r = random.Random()
        self.config = '/tmp/pwebs.config.%s.ini' % r.randint(1, 5000)
        with open(self.config, 'w') as configfile:
            configfile.write(config)

        self.parser = config

    def tearDown(self):
        import os
        os.remove(self.config)

    def test_valid_config(self):
        cparser = nagios.config(self.config)
        self.assertEqual(cparser.get('cabinet_01', 'username'), 'foo')
        self.assertEqual(cparser.get('cabinet_01', 'password'), 'secret')

    def test_invalid_config(self):
        with self.assertRaises(nagios.ArgumentTypeError):
            nagios.config('/etc/hosts')

    def test_unreadable_config(self):
        with self.assertRaises(nagios.ArgumentTypeError):
            nagios.config('/uidatre/dtiraen')


class TestOutputFile(unittest.TestCase):
    def test_output_stdout(self):
        import sys
        self.assertEqual(nagios.output_file('-'), sys.stdout)

    def test_unwriteable_file(self):
        with self.assertRaises(nagios.ArgumentTypeError):
            nagios.output_file('/foootirane654/diuraentiane')

    @unittest.skip('Will be skipped to avoid stupid things of stupid users.')
    def test_unsufficient_permission_on_output_file(self):
        with self.assertRaises(nagios.ArgumentTypeError):
            nagios.output_file('/etc/hosts')

    def test_writeable_file(self):
        tmp_file = '/tmp/pwebs.nagios.tests.cfg'
        f = nagios.output_file(tmp_file)
        self.assertEqual(tmp_file, f.name)


class TestNagiosConfigGenerator(unittest.TestCase):
    def setUp(self):
        import random
        r = random.Random()
        self._configfile = '/tmp/pwebs.config.%s.ini' % r.randint(1, 5000)
        self._invalid_configfile = self._configfile + '.invalid'
        with open(self._configfile, 'w') as configfile:
            configfile.write(config)
        invalid_conf = '''
[cabinet_01]
watch = invalid
'''
        with open(self._invalid_configfile, 'w') as invalidfile:
            invalidfile.write(invalid_conf)

        self.invalid_conf = nagios.config(self._invalid_configfile)

        self.config = nagios.config(self._configfile)

    def tearDown(self):
        import os
        os.remove(self._configfile)
        os.remove(self._invalid_configfile)

    def test__hosts(self):
        hosts = []
        nc = nagios.NagiosConfig(self.config)
        for h in nc._hosts():
            hosts.append(h)
        self.assertListEqual(hosts, ['cabinet_01', 'cabinet_02', '192.168.1.1'])

    def test__services(self):
        services = [('cabinet_01', 'water'), ('cabinet_01', 'air'),
                    ('cabinet_01', 'performance'), ('cabinet_02', 'water'),
                    ('cabinet_02', 'air'), ('192.168.1.1', 'air')
                    ]
        parsed_services = []
        nc = nagios.NagiosConfig(self.config)
        for host, service in nc._services():
            parsed_services.append((host, service))

        self.assertListEqual(services, parsed_services)

    def test__with_invalid_services(self):
        nc = nagios.NagiosConfig(self.invalid_conf)
        with self.assertRaises(nagios.InvalidService):
            for service in nc._services():
                pass
