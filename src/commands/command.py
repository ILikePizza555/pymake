command_map = {}

class CommandError(Exception):
    """
    Raised when a command encouters an error that can be resolved by the user. This is also the base
    class for exceptions in this package.
    """
    pass


class CommandParseError(CommandError):
    """
    Raised when a command encouters and error parsing user-provide input.

    Attributes:
        name -- Name of the command that caused the error
        expression -- The expression that caused the error
        message -- Explanation of the error
    """

    def __init__(self, name, expression, message):
        self.name = name
        self.expression = expression
        self.message = message
    
    def __str__(self):
        return f"{self.name}: parse error on {self.expression}: {self.message}"

def command(name: str):
    """
    A decorator the defines a command. 
    
    A command should be a callable that takes a list of strings that define arguments, 
    a dictionary definining environment variables, a file-like object representing the input stream, 
    and a file-like object representing the output stream.
    """
    def wrapper(func):
        if name in command_map:
            raise ValueError(f"Command {name} is already defined.")
        
        command_map[name] = func

        return func
    return wrapper