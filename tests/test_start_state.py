import mock
import pytest

from bioreactor_client.process_state_machine import AbortProcess, Start


def test_successful_start(mock_reactor):

    state_to_test = Start(next_state=mock.sentinel.next_state)

    next_state, reactor_status = state_to_test.next_state(mock_reactor)

    assert next_state == mock.sentinel.next_state

    # Also check that the state of the reactor was altered (input valve opened)
    mock_reactor.input_valve.open_valve.assert_called_once()


def test_start_with_input_open(mock_reactor):
    """Test that we detect error state 'input already open'"""

    state_to_test = Start(next_state=mock.sentinel.next_state)
    mock_reactor.input_valve.open_valve()

    with pytest.raises(AbortProcess):
        state_to_test.next_state(mock_reactor)


def test_start_with_output_open(mock_reactor):
    """Test that we detect error state 'output is opene'"""
    state_to_test = Start(next_state=mock.sentinel.next_state)
    mock_reactor.output_valve.open_valve()

    with pytest.raises(AbortProcess):
        state_to_test.next_state(mock_reactor)
