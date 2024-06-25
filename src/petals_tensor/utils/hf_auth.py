import os
from typing import Union


def always_needs_auth(model_name: Union[str, os.PathLike, None]) -> bool:
    """
    Check if a model always needs authentication

    Returns:
        Whether the model always needs authentication
    Args:
        model_name: The model name or path
    """

    loading_from_repo = model_name is not None and not os.path.isdir(model_name)
    return loading_from_repo and model_name.startswith("meta-llama/Llama-2-")
