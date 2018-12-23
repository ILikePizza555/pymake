from typing import List, Tuple, NamedTuple

def parse_dependency_line(line: str) -> Tuple[List[str], List[str]]:
    target_str, component_str = line.split(":")

    return (target_str.strip().split(" "), component_str.strip().split(" "))


class Rule(NamedTuple):
    """ Represents a makefile rule. """
    targets: List[str]
    components: List[str]
    recipe: List[str]

    @classmethod
    def parse_rule(cls, lines: List[str], recipe_prefix="\t") -> Tuple[Rule, List[str]]:
        """
        Parses a Rule from a list of lines. Assumes the first line is a dependency line.
        Returns a Rule and the remaining list of lines.
        """
        recipe = []
        targets, components = parse_dependency_line(lines.pop(0))

        while lines and lines[0].startswith(recipe_prefix):
            recipe.append(lines.pop(0))
        
        return (cls(targets, components, recipe), lines)


# Represents a makefile macro (or variable)
class Macro(NamedTuple):
    """
    Represents a makeifle macro (aka variable) line.
    """
    name: str 
    op: str
    value: str

    @classmethod
    def parse_macro(cls, lines: List[str], macro_op="=") -> Tuple[Macro, List[str]]:
        """
        Parses a macro from a single line.
        Returns a Macro object and the remaining lines
        """
        line = lines.pop(0)
        return (cls(*line.partition(macro_op)), lines)


def parse_file(f: str) -> list:
    lines = f.splitlines()
    rv = []

    while lines:
        # Ignore blank lines and comments
        if lines[0].startswith("#") or not lines[0].strip():
            lines.pop(0)
            continue
        
        if "=" in lines[0]:
            rv.append(Macro.parse_macro(lines)[0])
        else:
            rv.append(Rule.parse_rule(lines)[0])
    
    return rv