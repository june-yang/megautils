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

from ironic_python_agent import errors


class PathNotFound(errors.RESTError):
    """Error raised when path not found"""

    message = ('Path not found')


class MegaCLIError(errors.RESTError):
    """Error raised when megacli execute failed"""

    message = ('MegaCli execute failed!')



class InvalidParameterValue(errors.RESTError):
    """Error raised when an invalid parameter inputed"""

    message = ('An invalid parameter inputed!')

class InvalidDiskFormater(errors.RESTError):
    """Error raised when an invalid disk formater inputed"""
    message = ('An invalid disk formater inputed: %(disk)')


class RaidOperationError(errors.RESTError):
    """Error raised when raid operation error"""

    message = ('Raid operation error!')


class PhysicalDisksNotFoundError(errors.RESTError):
    """Error raised when require physical disk not found"""

    message = ('No available pyhsical disk found!')