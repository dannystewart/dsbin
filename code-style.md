Use modern type hinting exclusively (|, list, dict, etc., not Union, List, Dict)

Include type hints in code, but not in docstrings.

Use %s formatting in logger statements instead of f-strings. Use f-strings everywhere else.

Ensure that all log statements are pluralized correctly. If additional code is required (e.g. `"s" if len(files) != 1 else ""`) then please add it.

All docstrings and log messages MUST use proper sentence structure and punctuation, particularly at the end.

Arguments and returns should begin with "The" or "A" in most cases (e.g. "The list" or "A list" rather than "List").

Do your best to keep arguments and returns to a single line, but not at the expense of clarity.

Include comments explaining operations and steps are welcome when appropriate.

Docstrings should be formatted with Args/Returns/Raises section exactly as shown below:

"""Summary.

This can be a lengthier description if the function or method is sufficiently
complex, or to explain integration with other parts of the script or program.
Make sure to always use proper sentence structure and punctuation.

Args:
    arg: This is an argument.

Returns:
    This is what it returns.

Raises:
    ErrorType: This is an error it raises.
"""

Not all docstrings require all sections. Always include Raises if there are any, but some arguments or returns may be self-explanatory. Use concise one-line docstrings when the method's purpose and signature are obvious.
