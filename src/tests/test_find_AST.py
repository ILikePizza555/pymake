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

class TestExpr(object):
    def test_empty_tokens_throws_ValueError(self):
        with pytest.raises(ValueError):
            find.expr_from_tokens([])
    
    def test_invalid_tokens_throws_CommandParseError(self):
        toks = find.tokenize_operands("-o -a ( )".split())

        with pytest.raises(CommandParseError):
            find.expr_from_tokens(toks)

    def test_unclosed_parentheses_throws_CommandParseError(self):
        toks = find.tokenize_operands("( -1 -2 -3".split())

        with pytest.raises(CommandParseError):
            find.expr_from_tokens(toks)
    
    @pytest.mark.parametrize(("operands", "expected"), [
        ("( -1 a b c -2 )".split(), find.ASTBinOr),
        ("! -1 a b c".split(),      find.ASTBinNot),
        ("-1 a b c".split(),        find.ASTPrimary)
    ])
    def test_valid(self, operands, expected):
        toks = find.tokenize_operands(operands)

        actual = find.expr_from_tokens(toks)

        # Check the type because whether or not the subtree correctly parsed is not the scope of this test
        assert type(actual) is expected

class TestASTAnd(object):
    def test_empty_tokens_throws_ValueError(self):
        with pytest.raises(ValueError):
            find.ASTBinAnd.from_tokens([])

def test_big():
    tinput = "-1 a -2 b ! -3 c -o ( -4 -5 -o -6 )"
    expected = find.ASTBinOr([
        find.ASTBinAnd([
            find.ASTPrimary("1", ["a"]),
            find.ASTPrimary("2", ["b"]),
            find.ASTBinNot(
                find.ASTPrimary("3", ["c"])
            )
        ]),
        find.ASTBinAnd([
            find.ASTBinOr([
                find.ASTBinAnd([
                    find.ASTPrimary("4", []),
                    find.ASTPrimary("5", [])
                ]),
                find.ASTBinAnd([
                    find.ASTPrimary("6", [])
                ])
            ])
        ])
    ])

    assert find.ASTBinOr.from_tokens(find.tokenize_operands(tinput.split())) == expected