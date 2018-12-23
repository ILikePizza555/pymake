from make.parser import *
import pytest

class TestParseDependencyLine(object):
    def test_empty_str_throws_error(self):
        with pytest.raises(ValueError):
            parse_dependency_line("")

    def test_no_colon_throws_error(self):
        with pytest.raises(ValueError):
            parse_dependency_line("This is not a valid line.")

    @pytest.mark.parametrize("input_line,expected", [
        ("a:", (["a"], [])),
        ("a be c:", (["a", "be", "c"], [])),
        ("a : cat d   echo", (["a"], ["cat", "d", "echo"])),
        ("a   be  c:d   e first", (["a", "be", "c"], ["d", "e", "first"]))
    ])
    def test_valid(self, input_line, expected):
        actual = parse_dependency_line(input_line)
        assert actual == expected