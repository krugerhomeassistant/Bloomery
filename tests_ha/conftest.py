from pathlib import Path

import custom_components  # the plugin's testing_config package shadows ours; add our dir to it
import pytest

custom_components.__path__.append(str(Path(__file__).parents[1] / "custom_components"))


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield
