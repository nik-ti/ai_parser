from urllib.parse import urljoin
from bs4 import BeautifulSoup
import builtins

def execute_parsing_code(code: str, html_content: str, base_url: str = ""):
    """
    Executes the provided Python code in a sandboxed environment.
    The code has access to 'html_content' (str) and 'BeautifulSoup' (class).
    It must define a variable 'parsed'.
    """
    
    # Define the allowed builtins. 
    # We want to be very restrictive.
    allowed_builtins = {
        "len": builtins.len,
        "str": builtins.str,
        "int": builtins.int,
        "float": builtins.float,
        "list": builtins.list,
        "dict": builtins.dict,
        "set": builtins.set,
        "tuple": builtins.tuple,
        "bool": builtins.bool,
        "range": builtins.range,
        "enumerate": builtins.enumerate,
        "zip": builtins.zip,
        "min": builtins.min,
        "max": builtins.max,
        "sum": builtins.sum,
        "abs": builtins.abs,
        "sorted": builtins.sorted,
        "filter": builtins.filter,
        "map": builtins.map,
        "any": builtins.any,
        "all": builtins.all,
        "isinstance": builtins.isinstance,
        # Exception handling might be needed by the generated code?
        "Exception": builtins.Exception,
        "ValueError": builtins.ValueError,
        "TypeError": builtins.TypeError,
        "IndexError": builtins.IndexError,
        "KeyError": builtins.KeyError,
        "AttributeError": builtins.AttributeError,
    }

    # Global scope for the execution
    sandbox_globals = {
        "__builtins__": allowed_builtins,
        "BeautifulSoup": BeautifulSoup,
        "html_content": html_content,
        "urljoin": urljoin,
        "base_url": base_url,
    }
    
    # Local scope to capture variables defined by the code
    sandbox_locals = {}

    try:
        exec(code, sandbox_globals, sandbox_locals)
    except Exception as e:
        raise RuntimeError(f"Error executing generated code: {e}")

    if "parsed" not in sandbox_locals:
        raise RuntimeError("The generated code did not define the 'parsed' variable.")

    return sandbox_locals["parsed"]
