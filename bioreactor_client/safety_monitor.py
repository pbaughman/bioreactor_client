from .process_state_machine import AbortProcess


class SafetyMonitor:
    """Monitor safety critical parameters and ensure and abort if things get dangerous.

    This class serves as a backstop to the reactor state machine.
    Not every state monitors every parameter of the reaction.

    For example, it might be possible to have an over-pressure event while filling the reactor.

    The SafetyMonitor serves as a backstop to the main state machine
    """

    def __init__(self, max_pressure, max_temperature):
        self._max_pressure = max_pressure
        self._max_temperature = max_temperature

    def monitor_reactor_parameters(self, reactor_parameters):
        if reactor_parameters['temperature'] > self._max_temperature:
            raise AbortProcess("Safety critical parameter 'temperature' out of bounds")

        if reactor_parameters['pressure'] > self._max_pressure:
            raise AbortProcess("Safety critical parameters 'pressure' out of bounds")
