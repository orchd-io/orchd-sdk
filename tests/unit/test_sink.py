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

import pytest

from orchd_sdk.errors import SinkError
from orchd_sdk.models import SinkTemplate
from orchd_sdk.sink import sink_factory, DummySink, AbstractSink


def test_sink_factory():
    sink = sink_factory(DummySink.template)
    assert sink is not None
    assert isinstance(sink, AbstractSink) is True

    with pytest.raises(SinkError):
        template: SinkTemplate = DummySink.template.model_copy()
        template.sink_class = 'not.existent.Class'
        sink_factory(template)
