import pytest

from bioreactor_client.process_state_machine import AbortProcess
from bioreactor_client.safety_monitor import SafetyMonitor


def test_over_temperature(mock_reactor):

    safety_monitor = SafetyMonitor(max_pressure=200, max_temperature=100)

    # Sanity check that we don't raise when under max temperature
    mock_reactor.get_reactor_status()['temperature'] = 90
    safety_monitor.monitor_reactor_parameters(mock_reactor.get_reactor_status())

    # Check that we catch an over-temperature condition
    mock_reactor.get_reactor_status()['temperature'] = 110
    with pytest.raises(AbortProcess):
        safety_monitor.monitor_reactor_parameters(mock_reactor.get_reactor_status())
