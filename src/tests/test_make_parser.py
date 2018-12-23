from make.parser import parse_dependency_line, Rule, Macro, parse_file
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
        ("a:test", (["a"], ["test"])),
        ("a : cat d   echo", (["a"], ["cat", "d", "echo"])),
        ("a   be  c:d   e first", (["a", "be", "c"], ["d", "e", "first"]))
    ])
    def test_valid(self, input_line, expected):
        actual = parse_dependency_line(input_line)
        assert actual == expected

class TestParseRule(object):
    @pytest.mark.parametrize(("lines","expected"), [
        (["test:","\tfoobar.exe"], Rule(["test"], [], ["foobar.exe"])),
        (["test1 test2 test3:","\tfoobar.exe", "\tclean"], Rule(["test1", "test2", "test3"], [], ["foobar.exe", "clean"])),
        (["twilight: glimglam", "\tspike", "\tsunburst"], Rule(["twilight"], ["glimglam"], ["spike", "sunburst"])),
        (["twilight: rainbow dash", "\totp.exe"], Rule(["twilight"], ["rainbow", "dash"], ["otp.exe"])),
        (["apple jack : twilight rainbow dash", "\tfoobar.exe"], Rule(["apple", "jack"], ["twilight", "rainbow", "dash"], ["foobar.exe"]))
    ])
    def test_valid(self, lines, expected):
        actual = Rule.parse_rule(lines)
        assert actual == expected
    
    def test_no_target_throws_error(self):
        rule_lines = [": there is no target", "\tvalid_recipe.exe"]
        with pytest.raises(ValueError):
            Rule.parse_rule(rule_lines)
    
    def test_invalid_depedency_line_throws_error(self):
        rule_lines = ["Invalid depedency line", "\tvalid_recipe.exe"]
        with pytest.raises(ValueError):
            Rule.parse_rule(rule_lines)


class TestParseMacro(object):
    def test_valid(self):
        line = ["FOOBAR = test.c"]
        assert Macro.parse_macro(line) == Macro("FOOBAR", "=", "test.c")


SAMPLE_MAKE = """
# Comment
.SUFFIXES = .py

sample_target: requirement
    aaa
    bbb

requirement:
    ccc
    ddd
"""

SAMPLE_MAKE_EXPECTED = [
    Macro(".SUFFIXES", "=", ".py"), 
    Rule(["sample_target"], ["requirement"], ["aaa", "bbb"]), 
    Rule(["requirement"], [], ["ccc", "ddd"])
]

def test_parse_file():
    actual = parse_file(SAMPLE_MAKE)
    
    assert actual == SAMPLE_MAKE_EXPECTED