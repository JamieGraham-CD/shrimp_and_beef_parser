import json
import os

from Tools.tools import (
    google_search,
    scrape_website,
    scrape_website_handling_proxies
)


def get_tool_schemas():
    """
    Loads and returns the tool schemas from the `tools.json` file.

    This function reads the `tools.json` file located in the same directory as the script
    and loads its contents into a dictionary.

    Returns:
        dict: A dictionary containing tool schemas as loaded from the JSON file.
    """
    cwd = os.path.dirname(__file__)
    with open(f"{cwd}/tools.json") as f:
        return json.load(f)
    
def get_tool_by_name(name: str):
    """
    Retrieves a tool function based on its name.

    This function maps the provided name to a corresponding tool function. If the name matches
    one of the predefined tool functions, it returns that function; otherwise, it returns `None`.

    Args:
        name (str): The name of the tool function to retrieve.

    Returns:
        callable | None: The tool function corresponding to the given name, or `None` if no match is found.
    """
    if name == google_search.__name__:
        return google_search
    if name == scrape_website.__name__:
        return scrape_website
    if name == scrape_website_handling_proxies.__name__:
        return scrape_website_handling_proxies
    return None


def get_all_tools_by_names(tool_names: list[str]) -> list:
    """
    Retrieves a list of tool functions based on their names.

    This function takes a list of tool names and returns a corresponding list of tool functions.
    If any of the names do not match a known tool function, a `ValueError` is raised.

    Args:
        tool_names (list[str]): A list of names of the tool functions to retrieve.

    Returns:
        list[callable]: A list of tool functions corresponding to the provided names.

    Raises:
        ValueError: If one or more tool names are invalid and cannot be matched to any tool function.
    """
    tools = [get_tool_by_name(name) for name in tool_names]
    if None in tools:
        raise ValueError(
            f"Invalid tool name(s) provided: {tool_names}. One or more names could not be matched to a tool function."
        )
    return tools

def get_tool_from_list_by_name(tools: list, name: str):
    """
    Finds a tool function from a given list based on its name.

    This function searches through a provided list of tool functions and returns the function that
    matches the given name. If no matching function is found, it returns `None`.

    Args:
        tools (list[callable]): A list of tool functions to search through.
        name (str): The name of the tool function to find.

    Returns:
        callable | None: The tool function matching the provided name, or `None` if not found.
    """
    for tool in tools:
        if tool.__name__ == name:
            return tool
    return None


def generate_gpt_tools(tool_names: list[str]):
    """
    Generates a list of function specifications for GPTModel based on tool names.

    This function retrieves the tool schemas and creates a list of function specifications
    that GPTModel can use for function calling, based on the provided tool names.

    Args:
        tool_names (list[str]): A list of tool function names to include in the specifications.

    Returns:
        list[dict]: A list of dictionaries containing function specifications for the specified tools.
    """
    tool_schemas = get_tool_schemas()
    return [{"type": "function", "function": tool_schemas[tool]} for tool in tool_names]
