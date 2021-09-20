import pytest
import mock


class MockValve:

    def __init__(self):
        self._state = "closed"

    def get_valve_state(self):
        return self._state

    def open_valve(self):
        self._state = "open"
        return "open"

    def close_valve(self):
        self._state = "closed"
        return "closed"


@pytest.fixture(scope="function")
def mock_reactor():
    """Create an object that can be used in place of a real ReactorApiClient class."""
    mock_reactor = mock.Mock(
        spec_set=["get_reactor_status", "get_reactor_id", "input_valve", "output_valve"],
    )

    # Set some neutral return values on the mock.
    # Tests can override these, but these give a good baseline
    mock_reactor.get_reactor_id.return_value = 1
    mock_reactor.get_reactor_status.return_value = {
        "fill_percent": 0,
        "pH": 7,
        "pressure": 113,
        "temperature": 25.0
    }
    mock_reactor.input_valve = mock.Mock(wraps=MockValve())
    mock_reactor.output_valve = mock.Mock(wraps=MockValve())

    return mock_reactor
