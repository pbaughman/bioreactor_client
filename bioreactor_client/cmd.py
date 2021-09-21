import time

from .batch_record import BatchRecord, get_process_checks
from .process_state_machine import AbortProcess
from .process_state_machine import Start, FillReactor, RunReaction, EmptyReactor
from .reactor_api_client import get_reactor
from .safety_monitor import SafetyMonitor

# These could easily be passed in as arguments, or read in from a database or file
# but that seems beyond the scope of a coding exercise.
MIN_FILL = 68
MAX_FILL = 72
MAX_PRESSURE = 200
MIN_STOP_TEMP = 79
MAX_STOP_TEMP = 81


def main():

    # TODO: A slightly better (more readable) design would declare all of the states
    # with their process parameters like min temp, max temp, pressure, etc...
    # but not link them up to "next_state" in the first go-round,
    # Then construct a state machine where "next_state" is specified.
    # That would improve the clarity of this declaration.
    process_state = Start(
        next_state=FillReactor(
            min_fill=MIN_FILL,
            max_fill=MAX_FILL,
            next_state=RunReaction(
                pressure_limit=MAX_PRESSURE,
                min_stop_temp=MIN_STOP_TEMP,
                max_stop_temp=MAX_STOP_TEMP,
                next_state=EmptyReactor()
            )
        )
    )
    process_checks = get_process_checks(
            min_fill=MIN_FILL,
            max_fill=MAX_FILL,
            max_pressure=MAX_PRESSURE,
            min_stop_temp=MIN_STOP_TEMP,
            max_stop_temp=MAX_STOP_TEMP,
    )
    safety_monitor = SafetyMonitor(
        max_pressure=250,
        max_temperature=100,
    )
    reactor = get_reactor()
    process_data_monitor = BatchRecord()
    start = time.monotonic()
    print(f"Starting reaction in reactor {reactor.get_reactor_id()}")

    # TODO: In a real project, the below would be in its own method to make it easier to
    # write tests for.  It would take a state machine, a safety monitor, and a mock reactor as
    # an input.
    # It would return any reporting objects needed for batch traceability.
    try:
        # TODO: A real tool might have some watchdog that notices when a certain process step
        # is taking too long - maybe the batch fizzles and never reaches the correct temperature
        # range.
        # Here we're just going to print time stamps out to the console for a human to monitor.
        while not process_state.is_terminal_state():
            state_name = process_state.state_name()
            next_state, reactor_status = process_state.next_state(reactor)

            # Log all process data required for customers and regulatory compliance
            process_data_monitor.record_reactor_status(state_name, reactor_status)

            # As a back-stop to the main state machine, make sure none of our safety critical
            # parameters have gone out-of-bounds.
            # I'd expect the server-side of a real reaction control system to also be performing
            # this check
            safety_monitor.monitor_reactor_parameters(reactor_status)

            if process_state != next_state:
                t_now = round(time.monotonic() - start, 2)
                print(f"T={t_now}, Process State={next_state.state_name()}")
            process_state = next_state
            # Note - We are somewhat limited by the API here.
            # Sometimes it returns quite quickly, but sometimes there are delays on
            # the order of a quarter-second.
            # It's probably not worth trying to go much faster than this.
            time.sleep(0.35)

        # It seems like we made a successful batch!
        # The ultimate determination will need to be made by our reporting tools
        # but we successfully made it through all of the steps.
        run_process_checks(process_checks, process_data_monitor, True)

    except AbortProcess as abort_reason:
        print(f"Reaction aborted because of: {abort_reason}")
        reactor.input_valve.close()
        reactor.output_valve.open()

        # Do our best to print a report for the batch.
        # The most important thing is that our batch failed.
        # We might not have sufficient data on certain steps since we aborted early
        run_process_checks(process_checks, process_data_monitor, False)


def run_process_checks(process_checks, batch_record, process_completed):
    print("\n\n\n---------- Final Report ----------")

    failures = []

    for check in process_checks:
        success, msg = check(batch_record, process_completed).check_is_successful()
        print(msg)
        if not success:
            failures.append(msg)

    if failures:
        # Here you could highlight the failures again.
        # Alternatively you could set this up to only print failures
        print("The overall status of this batch is: FAILED")
    elif not process_completed:
        # This is defense-in-depth against the process_checks not handling
        # an incomplete process correctly.
        # With additional unit testing of the process checks, this becomes
        # unnecessary
        print("The overall status of this batch is: FAILED/INCOMPLETE")
    else:
        print("The overall status of this batch is: SUCCESS")
