# Copyright (C) 2014-2014 Project
# License: http://www.gnu.org/licenses/gpl.html GPL version 2 or higher

import unittest
from pwebs.rittal import Rittal


class TestRittal(unittest.TestCase):
    def test_equiv_cmclcp(self):
        content = '<html>\r\n\n<head>\r\n\n<meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">\r\n\n<title>LCP-Plus [192.168.1.200]</title>\r\n\n<meta http-equiv="refresh" content="0; URL=cmclcp.cgi?0030201021772199184">\r\n\n</head>\r\n\n<body></body>\r\n\n</html>\r\n'
        rittal = Rittal('localhost')
        url = rittal._equiv_cmclcp(content)
        self.assertEqual(url, 'cmclcp.cgi?0030201021772199184')

    def test_equiv_cmclogin(self):
        content = '<html>\r\n\n<head>\r\n\n<meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">\r\n\n<title>LCP-Plus [192.168.1.200]</title>\r\n\n<meta http-equiv="refresh" content="0; URL=cmclogin.cgi?0030201021772199184">\r\n\n</head>\r\n\n<body></body>\r\n\n</html>\r\n'
        rittal = Rittal('localhost')
        url = rittal._equiv_cmclogin(content)
        self.assertEqual(url, 'cmclogin.cgi?0030201021772199184')

    @unittest.skip('Tests requires rittal webserver running on localhost:8000')
    def test_login(self):
        import re
        rittal = Rittal('localhost:8000')
        login_html = rittal._login()
        self.assertFalse('Wrong user' in login_html, 'Got wrong user')

        success_line = r'<frame src="cmclcp.cgi[?][0-9]+" name="main" bordercolor=white frameborder=0 framespacing=0 scrolling=yes noresize\>'
        self.assertIsNotNone(re.search(success_line, login_html))
