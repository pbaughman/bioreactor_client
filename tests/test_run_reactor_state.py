import mock

from bioreactor_client.process_state_machine import RunReaction


def test_running(mock_reactor):

    state_to_test = RunReaction(
        pressure_limit=200,
        min_stop_temp=70,
        max_stop_temp=80,
        next_state=mock.sentinel.next_state
    )

    next_state, reactor_status = state_to_test.next_state(mock_reactor)

    assert next_state == state_to_test

# Additional test cases intentionally omitted in the interest of time.
# See `test_start_state.py` and `test_fill_state.py` to see a more complete set
# of unit tests.
# Because this is a coding exercice, test coverage is not as extensive as it would be
# for real production code.
