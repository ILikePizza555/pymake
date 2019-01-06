from commands.command import CommandParseError
from copy import deepcopy
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

    def test_look_before_eating(self):
        toks = find.tokenize_operands("-o -a ( )".split())
        toks_cpy = deepcopy(toks)

        with pytest.raises(CommandParseError):
            find.ASTPrimary.from_tokens(toks)

        assert toks == toks_cpy

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

class TestASTExpr(object):
    def test_empty_tokens_throws_ValueError(self):
        with pytest.raises(ValueError):
            find.ASTExpr.from_tokens([])
    
    def test_invalid_tokens_throws_CommandParseError(self):
        toks = find.tokenize_operands("-o -a ( )".split())

        with pytest.raises(CommandParseError):
            find.ASTExpr.from_tokens(toks)

    def test_unclosed_parentheses_throws_CommandParseError(self):
        toks = find.tokenize_operands("( -1 -2 -3".split())

        with pytest.raises(CommandParseError):
            find.ASTExpr.from_tokens(toks)
    
    @pytest.mark.parametrize(("operands", "expected"), [
        ("( -1 a b c -2 )".split(), find.ASTBinOr),
        ("! -1 a b c".split(),      find.ASTBinNot),
        ("-1 a b c".split(),        find.ASTPrimary)
    ])
    def test_valid(self, operands, expected):
        toks = find.tokenize_operands(operands)

        actual = find.ASTExpr.from_tokens(toks)

        # Check the type because whether or not the subtree correctly parsed is not the scope of this test
        assert type(actual.value) is expected