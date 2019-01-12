import string
import re
from typing import List, Union, Set, Generator, Iterable


def bracket_expantion(b: str) -> set:
    match = re.fullmatch(r"\[:(.*):\]", b)
    if match is not None:
        # Named character class
        return {
            "alnum": set(string.ascii_letters) | set(string.digits),
            "alpha": set(string.ascii_letters),
            "blank": set(" \t"),
            "cntrl": set(chr(177)) | set([chr(i) for i in range(0, 31)]),
            "digit": set(string.digits),
            "graph": set(string.digits) | set(string.ascii_letters) | set(string.punctuation),
            "lower": set(string.ascii_lowercase),
            "print": set(string.printable),
            "punct": set(string.punctuation),
            "space": set(string.whitespace),
            "upper": set(string.ascii_uppercase),
            "xdigit": set(string.hexdigits)
        }[match.group(1)]

    # Remove the brackets and test to see if we're inverting
    unwrapped = b.strip("[]")
    if unwrapped[0] == "!" or unwrapped[0] == "^":
        inverse = True
        unwrapped = unwrapped[1:]

    rv = set()
    # Loop over all single character or ranges (two characters separated by a dash)
    for m in re.finditer(r"(?:.\-.)|.", unwrapped):
        if len(m.group(0)) == 1:
            # Single character, add it to the set
            rv.add(m.group(0))
        else:
            # Range, split into two characters, then iterate between the ascii codes
            lower, upper = m.group(0).split("-")
            for c in range(ord(lower), ord(upper) + 1):
                rv.add(chr(c))

    if inverse:
        return set(string.printable) - rv
    return rv


def recursive_shell_match(input_str: str, pattern: List[Union[str, set]]) -> bool:
    if not input_str and not pattern:
        return True

    if pattern == ["*"]:
        return True

    if pattern[0] == "?":
        return recursive_shell_match(input_str[1:], pattern[1:])

    if pattern[0] == "*":
        return recursive_shell_match(input_str[1:], pattern[1:] if input_str[0] in pattern[1] else pattern)

    if input_str[0] in pattern[0]:
        return recursive_shell_match(input_str[1:], pattern[1:])

    return False


def expand_pattern(string: str, pattern: str) -> Generator[Union[Set[str], str]]:
    for m in re.finditer(pattern, string):
        if len(m.group(0)) == 1:
            yield m.group(0)
        else:
            yield bracket_expantion(m.group(0))


def shell_pattern_match(input_str: Union[str, Iterable[str]], pattern: str) -> Union[bool, List[bool]]:
    """
    Matches a pattern against an input using Unix Shell Pattern matching notation.
    ? matches any character
    * matches multiple characters
    [string] matches all characters that are members of string.

    Multiple input strings may be provided.
    """
    # Convert our input string to a list of characters and sets
    pattern_expansion = list(expand_pattern(pattern, r"\[.+\]|."))

    try:
        return [recursive_shell_match(i, pattern_expansion) for i in input_str]
    except TypeError:
        return recursive_shell_match(input_str, pattern_expansion)
