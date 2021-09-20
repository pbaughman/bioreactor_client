class AbortProcess(Exception):
    """A custom exception that makes it easier for any process state (below) to abort.

    All bioreactor processes have the same abort logic - open the output valve and discard the
    batch.

    Rather than plumbing this into the FSM itself, any state can raise this exception and the
    top level executor can execute the abort steps
    """
    pass


class ProcessState:
    """An abstract base class for process steps designed to implement a simple bioreactor process.

    Strictly speaking, for this example a finite state machine is not necessary.
    The process is so simple that it could easily be written in an imperative way.

    Using a FSM here is more complicated and possibly harder to test.

    On the flip side here, the FSM makes it easier to write unit tests for the process.
    It also makes it easier to make small changes to support more complicated processes.
    """

    def next_state(self, reactor):
        """Get a ProcessState object representing the next step of the process.

        Parameters
        ----------
        A ReactorApiClient used to control the reactor and poll the current reactor parameters.

        Returns
        -------
        A tuple of (ProcessState, dict): Where the dict contains the current bioreactor status
            parameters.  The dict is intended to be used for checking of critical process
            params.
        """
        raise NotImplementedError("Abstract method not implemented")

    def state_name(self):
        raise NotImplementedError("Abstract method not implemented")

    def is_terminal_state(self):
        """A way for the top level runner to know it's time to stop calling "next_state"

        Returns
        -------
        True if the state is terminal and the runner can stop
        """
        raise NotImplementedError("Abstract method not implemented")


class Start(ProcessState):

    def __init__(self, next_state):
        self._next_state = next_state

    def state_name(self):
        return "start"

    def is_terminal_state(self):
        return False

    def next_state(self, reactor):
        """Do some pre-flight checks of the reactor, then open the input valve.
        """
        # Do some pre-flight sanity checks on the reactor before kicking off the process
        if reactor.input_valve.get_valve_state() != "closed":
            raise AbortProcess("Attempted to start process but input valve was already open")
        if reactor.output_valve.get_valve_state() != "closed":
            raise AbortProcess("Attempted to start process but output valve was open")

        initial_state = reactor.get_reactor_status()
        reactor.input_valve.open_valve()
        return self._next_state, initial_state


class FillReactor(ProcessState):

    def __init__(self, min_fill, max_fill, next_state):
        self._min_fill = min_fill
        self._max_fill = max_fill
        self._next_state = next_state

    def state_name(self):
        return "fill"

    def is_terminal_state(self):
        return False

    def next_state(self, reactor):
        """Wait until the reactor reaches the specified fill level.
        """
        # TODO: An improved design with some defense in depth against bad state machines might
        # be to have some sanity check code that runs once the first time 'next_state' is called
        # to ensure the reactor state is what we expect - for example the valves we expect to be
        # open are open and the valves we expect to be closed are closed.
        # It would bombard the API if we check it every time `next_state` is called.
        # Checking once would be a good design compromise
        status = reactor.get_reactor_status()
        fill_percent = status['fill_percent']
        if fill_percent < self._min_fill:
            # Still filling
            return self, status
        if fill_percent <= self._max_fill:
            reactor.input_valve.close_valve()
            return self._next_state, status
        if fill_percent > self._max_fill:
            raise AbortProcess("Reactor over-filled")

        # The above should handle all cases.
        # Pop a runtime here because a logic error has occured
        raise RuntimeError("FillReactor state contains a logic error")


class RunReaction(ProcessState):

    def __init__(self, pressure_limit, min_stop_temp, max_stop_temp, next_state):
        self._pressure_limit = pressure_limit
        self._min_stop_temp = min_stop_temp
        self._max_stop_temp = max_stop_temp
        self._next_state = next_state

    def state_name(self):
        return "run"

    def is_terminal_state(self):
        return False

    def next_state(self, reactor):
        reactor_status = reactor.get_reactor_status()
        pressure = reactor_status['pressure']
        temperature = reactor_status['temperature']

        if pressure > self._pressure_limit:
            raise AbortProcess("Reactor over-pressure")

        if temperature < self._min_stop_temp:
            # Still waiting for temperature to reach desired range
            return self, reactor_status

        if temperature <= self._max_stop_temp:
            # We've reached the desired temperature
            reactor.output_valve.open_valve()
            return self._next_state, reactor_status

        if temperature > self._max_stop_temp:
            # TODO: Get clarity as to the desired behavior here.
            # The specification does not say what to do for an over-temperature state.
            # To be safe, abort the reaction
            raise AbortProcess("Reactor over-temperature")


class EmptyReactor(ProcessState):

    def __init__(self):
        pass

    def state_name(self):
        return "empty"

    def is_terminal_state(self):
        return False

    def next_state(self, reactor):
        """Wait until all product has drained from the reactor..
        """
        reactor_status = reactor.get_reactor_status()
        fill_percent = reactor_status["fill_percent"]
        if fill_percent > 0:
            return self, reactor_status
        else:
            return Done(), reactor_status


class Done(ProcessState):

    def __init__(self):
        pass

    def state_name(self):
        return "done"

    def is_terminal_state(self):
        return True

    def next_state(self, reactor):
        raise RuntimeError("Done is a terminal process state")
