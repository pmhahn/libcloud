# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import socket
import tempfile

from mock import Mock, patch, MagicMock

from libcloud.utils.py3 import httplib
from libcloud.common.base import Connection
from libcloud.common.base import Response
from libcloud.common.exceptions import RateLimitReachedError
from libcloud.test import unittest

CONFLICT_RESPONSE_STATUS = [
    ('status', '429'), ('reason', 'CONFLICT'),
    ('retry_after', '3'),
    ('content-type', 'application/json')]
SIMPLE_RESPONSE_STATUS = ('HTTP/1.1', 429, 'CONFLICT')


class FailedRequestRetryTestCase(unittest.TestCase):

    def _raise_socket_error(self):
        raise socket.gaierror('')

    def test_retry_connection(self):
        con = Connection(timeout=1, retry_delay=0.1)
        con.connection = Mock()
        connect_method = 'libcloud.common.base.Connection.request'

        with patch(connect_method) as mock_connect:
            try:
                mock_connect.side_effect = socket.gaierror('')
                con.request('/')
            except socket.gaierror:
                pass
            except Exception:
                self.fail('Failed to raise socket exception')

    def test_rate_limit_error(self):
        sock = Mock()
        con = Connection()

        try:
            with patch('libcloud.utils.py3.httplib.HTTPResponse.getheaders',
                       MagicMock(return_value=CONFLICT_RESPONSE_STATUS)):
                with patch(
                        'libcloud.utils.py3.httplib.HTTPResponse._read_status',
                        MagicMock(return_value=SIMPLE_RESPONSE_STATUS)):
                    with tempfile.TemporaryFile(mode='w+b') as f:
                        f.write('HTTP/1.1 429 CONFLICT\n'.encode())
                        f.flush()
                        sock.makefile = Mock(return_value=f)
                        mock_obj = httplib.HTTPResponse(sock)
                        mock_obj.begin()
                        Response(mock_obj, con)
        except RateLimitReachedError:
            pass
        except Exception:
            self.fail('Failed to raise Rate Limit exception')

if __name__ == '__main__':
    unittest.main()
