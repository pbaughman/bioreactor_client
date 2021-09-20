import time

from .process_state_machine import AbortProcess
from .process_state_machine import Start, FillReactor, RunReaction, EmptyReactor
from .reactor_api_client import get_reactor
from .safety_monitor import SafetyMonitor


def main():

    # TODO: A slightly better (more readable) design would declare all of the states
    # with their process parameters like min temp, max temp, pressure, etc...
    # but not link them up to "next_state" in the first go-round,
    # Then construct a state machine where "next_state" is specified.
    # That would improve the clarity of this declaration
    process_state = Start(
        next_state=FillReactor(
            min_fill=68,  # Specification here is 70 +/- 2
            max_fill=72,
            next_state=RunReaction(
                pressure_limit=200,
                min_stop_temp=79,  # Specification here is 80 +/- 1
                max_stop_temp=81,
                next_state=EmptyReactor()
            )
        )
    )

    safety_monitor = SafetyMonitor(
        max_pressure=250,
        max_temperature=100,
    )
    reactor = get_reactor()
    print(f"Starting reaction in reactor {reactor.get_reactor_id()}")

    # TODO: In a real project, the below would be in its own method to make it easier to
    # write tests for.  It would take a state machine, a safety monitor, and a mock reactor as
    # an input.
    # It would return any reporting objects needed for batch traceability.
    try:
        while not process_state.is_terminal_state():
            state_name = process_state.state_name()
            next_state, reactor_status = process_state.next_state(reactor)

            # Logging (added later)
            # For now, just dump to console so we can see what's happening
            import pprint
            print(state_name)
            pprint.pprint(reactor_status)

            # As a back-stop to the main state machine, make sure none of our safety critical
            # parameters have gone out-of-bounds.
            # I'd expect the server-side of a real reaction control system to also be performing
            # this check
            safety_monitor.monitor_reactor_parameters(reactor_status)

            # Now tick the state machine forward
            process_state = next_state
            time.sleep(0.5)

    except AbortProcess as abort_reason:
        print(f"Reaction aborted because of: {abort_reason}")
        reactor.input_valve.close()
        reactor.output_valve.open()
