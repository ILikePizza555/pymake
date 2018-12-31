from commands.echo import echo
from io import StringIO
import pytest

def test_echo():
    test_str = "Hello World!\n"

    output = StringIO()
    result = echo(test_str.strip().split(), {}, StringIO(), output)

    assert output.getvalue() == test_str
    assert result == 0

def test_echo_empty():
    output = StringIO()
    result = echo([], {}, StringIO(), output)

    assert output.getvalue() == "\n"
    assert result == 0