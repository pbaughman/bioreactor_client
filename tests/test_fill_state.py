import mock
import pytest

from bioreactor_client.process_state_machine import AbortProcess, FillReactor


def test_filling(mock_reactor):

    state_to_test = FillReactor(
        min_fill=50,
        max_fill=60,
        next_state=mock.sentinel.next_state
    )

    next_state, reactor_status = state_to_test.next_state(mock_reactor)

    assert next_state == state_to_test


def test_overfilled(mock_reactor):

    state_to_test = FillReactor(
        min_fill=50,
        max_fill=60,
        next_state=mock.sentinel.next_state
    )

    mock_reactor.get_reactor_status()['fill_percent'] = 61

    with pytest.raises(AbortProcess):
        state_to_test.next_state(mock_reactor)


def test_filled_correctly(mock_reactor):

    state_to_test = FillReactor(
        min_fill=50,
        max_fill=60,
        next_state=mock.sentinel.next_state
    )

    mock_reactor.get_reactor_status()['fill_percent'] = 55

    next_state, reactor_status = state_to_test.next_state(mock_reactor)

    assert next_state == mock.sentinel.next_state

    # Important! Also check that the state of the reactor was altered (input valve closed)
    mock_reactor.input_valve.close_valve.assert_called_once()
