# Copyright 2016 Mellanox Technologies, Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import subprocess

from megautils import exception

MEGACLI_PATH = '/opt/MegaRAID/MegaCli/MegaCli64'

class Mega(object):

    def __init__(self, path=MEGACLI_PATH):
        self.cli_path = path

        if not os.path.exists(path):
            raise exception.PathNotFound('path {0} not found'.format(path))

    def command(self, cmd):
        """
        Execute a megacli command
        :param cmd: 
        :return: 
        """
        proc = subprocess.Popen("{0} {1} -NoLog".
                                format(self.cli_path, cmd),
                                shell=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        out, err = proc.communicate()
        if isinstance(out, bytes):
            out = out.decode()
        if isinstance(err, bytes):
            err = err.decode()

        if proc.returncode:
            ex = exception.MegaCLIError(err.rstrip())
            ex.exitcode = proc.returncode
            raise ex
        return out

