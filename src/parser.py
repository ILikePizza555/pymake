from collections import namedtuple
from typing import List

# Represents a makefile Rule
Rule = namedtuple("Rule", ["targets", "components", "recipe"])
# Represents a makefile macro (or variable)
Macro = namedtuple("Macro", ["name", "op", "value"])