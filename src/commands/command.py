command_map = {}

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