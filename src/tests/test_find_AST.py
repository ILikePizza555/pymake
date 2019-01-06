from commands.command import CommandParseError
import commands.find as find
import pytest

class TestASTPrimary(object):
    def test_empty_tokens_throws_ValueError(self):
        with pytest.raises(ValueError):
            find.ASTPrimary.from_tokens([])
    
    def test_invalid_tokens_throws_CommandParseError(self):
        toks = find.tokenize_operands("-o -a ( )".split())

        with pytest.raises(CommandParseError):
            find.ASTPrimary.from_tokens(toks)

    @pytest.mark.parametrize(("tinput", "expected", "remainder"), [
        (find.tokenize_operands(["-test"]),                             find.ASTPrimary("test", []),            []),
        (find.tokenize_operands(["-test", "a", "b"]),                   find.ASTPrimary("test", ["a", "b"]),    []),
        (find.tokenize_operands(["-test1", "-test2"]),                  find.ASTPrimary("test1", []),           [(find.OperandTokens.OPERAND_NAME, "test2")]),
        (find.tokenize_operands(["-test1", "a", "b", "-test2"]),        find.ASTPrimary("test1", ["a", "b"]),   [(find.OperandTokens.OPERAND_NAME, "test2")]),
        (find.tokenize_operands(["-test1", "a", "(", "b", "-test2"]),   find.ASTPrimary("test1", ["a"]),        [(find.OperandTokens.LPAREN, "("), (find.OperandTokens.OPERAND_VALUE, "b"), (find.OperandTokens.OPERAND_NAME, "test2")])
    ])
    def test_valid(self, tinput, expected, remainder):
        actual = find.ASTPrimary.from_tokens(tinput)
        assert actual == expected
        assert tinput == remainder