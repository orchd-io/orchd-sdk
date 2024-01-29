# The MIT License (MIT)
# Copyright © 2022 <Mathias Santos de Brito>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


class InvalidInputError(Exception):
    """
    Invalid input given.
    """


class ReactorError(Exception):
    """Raise on internal Errors in the Reactor."""


class SinkError(Exception):
    """ Raised on Sink errors."""


class ReactionError(Exception):
    """ Raised on Reaction Management and Operation errors."""


class ReactionHandlerError(Exception):
    """ Raised by ReactionHandler implementations."""


class SensorError(Exception):
    """ Raised by Sensors to indicate an not fatal error."""


class SensorFatalError(Exception):
    """ Sensor fatal error. Sensor will not be available anymore."""


class InvalidRequestError(Exception):
    """ Raised when the request is invalid."""


class NotFoundError(Exception):
    """ Raised when the resource is not found."""


class ServerError(Exception):
    """ Raised when the server is not available."""


def handle_http_errors(response):
    if response.status == 404:
        raise NotFoundError()
    elif response.status == 400 or response.status == 422:
        raise InvalidRequestError()
    elif response.status == 500:
        raise ServerError()
    elif response.status > 400:
        raise Exception(response.status, response.reason)
    return response