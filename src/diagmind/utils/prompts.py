from importlib import resources


def load_prompt(name: str) -> str:
    """Read a prompt file packaged under diagmind.prompts."""
    return resources.files("diagmind.prompts").joinpath(name).read_text()

