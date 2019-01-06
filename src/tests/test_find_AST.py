from commands.find import ASTPrimary, ASTExpr, ASTBinNot, ASTBinOr, ASTBinAnd
import pytest

class TestASTPrimary(object):
    def test_empty_tokens_throws_error