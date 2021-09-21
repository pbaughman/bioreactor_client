from bioreactor_client.process_state_machine import EmptyReactor


def test_emptying(mock_reactor):

    state_to_test = EmptyReactor()

    mock_reactor.get_reactor_status()['fill_percent'] = 10

    next_state, reactor_status = state_to_test.next_state(mock_reactor)

    assert next_state == state_to_test

# Additional test cases intentionally omitted in the interest of time.
# See `test_start_state.py` and `test_fill_state.py` to see a more complete set
# of unit tests.
# Because this is a coding exercise, test coverage is not as extensive as it would be
# for real production code.
