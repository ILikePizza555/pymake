from typing import List, Tuple, NamedTuple


def parse_dependency_line(line: str) -> Tuple[List[str], List[str]]:
    if ":" not in line:
        raise ValueError(f"Expected a ':' after '{line}'")

    target_str, component_str = line.split(":")

    return (target_str.strip().split(), component_str.strip().split())


class Rule(NamedTuple):
    """ Represents a makefile rule. """
    targets: List[str]
    components: List[str]
    recipe: List[str]

    @classmethod
    def parse_rule(cls, lines: List[str], recipe_prefix="\t") -> "Rule":
        """
        Parses a Rule from a list of lines. Assumes the first line is a dependency line.
        Returns a Rule.
        """
        recipe = []
        l = lines.pop(0)
        targets, components = parse_dependency_line(l)
        if not targets:
            raise ValueError(f"Expected a target before '{l}'")

        while lines and lines[0].startswith(recipe_prefix):
            recipe.append(lines.pop(0).strip())
        
        return cls(targets, components, recipe)


# Represents a makefile macro (or variable)
class Macro(NamedTuple):
    """
    Represents a makeifle macro (aka variable) line.
    """
    name: str 
    op: str
    value: str

    @classmethod
    def parse_macro(cls, lines: List[str], macro_op="=") -> "Macro":
        """
        Parses a macro from a single line.
        Returns a Macro object
        """
        line = lines.pop(0)
        return cls(*line.partition(macro_op))


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