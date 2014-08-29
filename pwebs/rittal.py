# Copyright (C) 2014-2014 Project
# Author: Philipp Offensand
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher

import logging


class RittalLoginError(Exception):
    pass


class RittalDataError(Exception):
    pass


class Rittal:
    def __init__(self, host, user='monitor', password='monitor'):
        self._log = logging.getLogger('pwebs.rittal.Rittal')
        self.host = host
        self.user = user
        self.password = password
        self.data = None

    def _cmc_login(self, cmd):
        from urllib import request
        r = request.urlopen(
            'http://%s/%s' % (self.host, cmd),
        )
        html = r.read().decode('utf8')
        self._equiv_cmclcp(html)
        return html

    def _cmc_data(self, html):
        from urllib import request
        cmd = self._equiv_cmclcp(html)
        r = request.urlopen(
            'http://%s/%s' % (self.host, cmd),
        )
        html = r.read().decode('utf8')
        return html

    def _login(self):
        ''' String mit der erhalten Seite nach dem Login.
        '''
        from urllib import request
        r = request.urlopen(
            'http://%s/cmclogin.cgi?0210201000000000000' % self.host,
            data=b'p0404=monitor&p0405=monitor&ok=Login'
        )
        html = r.read().decode('utf8')
        cmd = self._equiv_cmclogin(html)
        html = self._cmc_login(cmd)
        self._log.debug('Got the following HTML Content after login:\n%s' % html)
        return html

    def _get_node_text(self, node):
        rc = ''
        if node.nodeType == node.TEXT_NODE:
            rc = node.data
        return rc

    def _get_value_mappings(self, row):
        mapping = dict()
        desc_node_id = 'bb12l'
        value_node_id = 'bb14r'
        unit_node_id = 'bb14l'
        desc_node = None
        value_node = None
        unit_node = None
        for cell in row.getElementsByTagName('td'):
            cell_id = cell.getAttribute('id')
            if cell_id == desc_node_id:
                desc_node = cell
            elif cell_id == value_node_id:
                value_node = cell
            elif cell_id == unit_node_id:
                unit_node = cell
        if desc_node and value_node and unit_node:
            mapping['desc'] = self._get_node_text(desc_node.firstChild.firstChild)
            mapping['value'] = self._get_node_text(value_node.firstChild)
            mapping['unit'] = self._get_node_text(unit_node.firstChild)
        return mapping

    def _get_dom(self, content):
        import lxml.sax
        from lxml import etree
        from xml.dom.pulldom import SAX2DOM
        parser = etree.HTMLParser()
        tree = etree.fromstring(content, parser=parser)
        handler = SAX2DOM()
        lxml.sax.saxify(tree, handler)
        return handler.document

    def get_data(self):
        data = dict()
        html = self._login()
        content = self._cmc_data(html)
        xmldoc = self._get_dom(content)
        rows = xmldoc.getElementsByTagName('tr')
        for row in rows:
            if row.hasChildNodes():
                mapping = self._get_value_mappings(row)
                try:
                    data[mapping['desc']] = (mapping['value'], mapping['unit'])
                except KeyError:
                    pass  # don't care here, may have got an uninteresting row...
        self.data = data
        self._log.debug('received data: \n%s' % data)
        return data

    def _get_data_value(self, value):
        if not self.data:
            self.get_data()
        return self.data[value]

    @property
    def water_in(self):
        return self._get_data_value('Water-In-Temperat.')

    @property
    def water_out(self):
        return self._get_data_value('Water-Out-Temperat.')

    @property
    def air_in(self):
        return self._get_data_value('Server-In-Temperat.')

    @property
    def air_out(self):
        return self._get_data_value('Server-Out-Temperat.')

    @property
    def setpoint(self):
        return self._get_data_value('Setpoint')

    @property
    def cooling_capacity(self):
        return self._get_data_value('Cooling Capacity')

    @property
    def waterflow(self):
        return self._get_data_value('Waterflow')

    @property
    def control_valve(self):
        return self._get_data_value('Control Valve')

    def _equiv_cmclcp(self, content):
        import re
        url_match = re.findall(r'(cmclcp.cgi[?][0-9]+)', content)
        if not url_match:
            raise RittalDataError('Unable to find the link to the data!')
        return url_match[0]

    def _equiv_cmclogin(self, content):
        import re
        url_match = re.findall(r'(cmclogin.cgi[?][0-9]+)', content)
        if not url_match:
            raise RittalLoginError('Unable to find the login-page!')
        return url_match[0]
