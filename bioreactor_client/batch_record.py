import collections
import datetime
from functools import partial

MinMax = collections.namedtuple('MinMax', ['min', 'max'])


class BatchRecord:
    """Records all process parameters and timestamps for a given batch..

    When running the reaction, this class can be used to record details about the process
    and then later be turned into a BatchReport which will give information about or critical
    process parameters.

    Storage is cheap, so I'd expect all of this information to be persisted to a database
    in a real project and then generate the BatchReport on-demand since details about what's
    in a BatchReport may change as business needs change.
    """

    def __init__(self):
        # Each reading is a three-tuple of (timestamp, process step, reactor_data)
        # Where timestamp is a DateTime object (in UTC)
        # process step is a step name like "fill" "run" from the process state machine
        # And the reactor readings are the data returned by the get_reactor_status() API
        self._readings = []

    def record_reactor_status(self, process_step, reactor_status):
        """Add the reading from a reactor to the BatchRecord."""
        self._readings.append((datetime.datetime.utcnow(), process_step, reactor_status))

    def get_process_steps(self):
        """Get the set of unique process steps covered by this BatchRecord."""

        # The batch records we're dealing with here are all short enough that it doesn't really
        # matter that we're iterating them every time we call this method.
        # If we wanted to, we could calculate this information every time 'record_reactor_status'
        # is called, and then we'd be able to retrieve the information faster.
        # Here I've opted for worse performance, but simpler implementation.
        # Most of the methods in this class have the same trade off made.

        return set(r[1] for r in self._readings)

    def process_duration(self):
        """Gets the time elapsed between the first reading and the last

        Returns
        -------
        A datetime.TimeDelta object
        """
        return self._readings[-1][0] - self._readings[0][0]

    def filter_by_step_name(self, step_name):
        """Generate a BatchRecord for a subset of the process steps covered by this BatchRecord.

        Parameters
        ----------
        step_name: str or list(str)
            A string, or a list of strings of the step names to include in the new BatchRecord

        Returns
        -------
        A new BatchRecord created from this one, but with only the specified step name(s) included

        """

        if isinstance(step_name, str):
            step_name = [step_name]

        filtered_record = BatchRecord()
        filtered_record._readings = [
            r
            for r
            in self._readings
            if r[1] in step_name
        ]
        return filtered_record

    def get_reading_range(self, reading_name):
        """Get the min and max value of a particular reading

        Parameters
        ----------
        reading_name: str
            The name of a reading returned by the get_reactor_status API, like `temperature`

        Returns
        -------
        A tuple of (min, max) value for the specified reading
        """
        # Again, we're not being super performant here.
        # See the note under the get_process_steps method
        return MinMax(
            min(r[2][reading_name] for r in self._readings),
            max(r[2][reading_name] for r in self._readings)
        )


# TODO: A real implementation would get this information from a file or a database,
# as there would be different process checks for different types of batches.
# In this case, we're just going to return the checks for the process we've been asked
# to implement but this is designed to be extensible.
def get_process_checks(min_fill, max_fill, max_pressure, min_stop_temp, max_stop_temp):
    # TODO - could do a better job with default arguments here when they're not needed
    return [
        partial(ProcessCompleted, MinMax(0, 0)),
        partial(FillLevelReached, MinMax(min_fill, max_fill)),
        partial(FillLevelMaintained, MinMax(min_fill, max_fill)),
        partial(TemperatureRange, MinMax(0, 0)),
        partial(TargetTemperatureReached, MinMax(min_stop_temp, max_stop_temp)),
        partial(PhRange, MinMax(0, 0)),
        partial(PressureRange, MinMax(0, max_pressure)),
        partial(PressureMaximum, MinMax(0, max_pressure)),
        partial(RunTime, MinMax(0, 0)),
    ]


class ProcessCheck:

    def __init__(self, process_limit, batch_record, process_completed):
        self._process_limit = process_limit
        self._batch_record = batch_record
        self._process_completed = process_completed

    def check_is_successful(self):
        """
        Returns
        -------
        A tuple of (bool, str)
            The boolean indicates whether or not the check was successful
            The string is intended to be a human-readable explanation
        """
        raise NotImplementedError("Abstract method not implemented")

    def is_within_limit(self, value):
        return value >= self._process_limit.min and value <= self._process_limit.max


class ProcessCompleted(ProcessCheck):

    def check_is_successful(self):
        if self._process_completed:
            return True, "Process ran until the end"
        else:
            return False, "Process was aborted early"
        return self._process_completed


class FillLevelReached(ProcessCheck):

    def check_is_successful(self):
        if "fill" not in self._batch_record.get_process_steps():
            return False

        # Check that we got all the way up to the specified fill range
        # in the fill step first
        fill_level_range = (self._batch_record
                            .filter_by_step_name("fill")
                            .get_reading_range('fill_percent'))

        msg = f"Max level reached during fill stage was {fill_level_range.max}"

        if not self.is_within_limit(fill_level_range.max):
            return False, msg
        return True, msg


class FillLevelMaintained(ProcessCheck):

    def check_is_successful(self):
        if "run" not in self._batch_record.get_process_steps():
            return False, "No run level data during 'run' stage"

        # Check that we remain within the limits during the 'run' stage
        level_range = (self._batch_record
                       .filter_by_step_name("run")
                       .get_reading_range('fill_percent'))

        if not self.is_within_limit(level_range.min):
            return False, f"CPP out of range. Fill level got too low: {level_range.min}%"
        if not self.is_within_limit(level_range.max):
            return False, f"CPP out of range. Fill level got too high: {level_range.max}%"

        return True, f"CPP Met. Fill level during run was {level_range.min}% to {level_range.max}%"


class TemperatureRange(ProcessCheck):

    def check_is_successful(self):
        # Here we're not actually checking anything.
        # We're just reporting the temperature range throughout the whole process
        temp_range = self._batch_record.get_reading_range("temperature")

        return True, f"Temperature ranged from {temp_range.min} to {temp_range.max}"


class TargetTemperatureReached(ProcessCheck):

    def check_is_successful(self):
        if "run" not in self._batch_record.get_process_steps():
            return False, "No run temperature data during 'run' stage"

        # Check that we achieved a maximum temperature within the target range
        # Note, we check "empty" here too incase things continue to heat up
        # while we drain the tank.
        temp_range = (self._batch_record
                      .filter_by_step_name(["run", "empty"])
                      .get_reading_range("temperature"))

        if not self.is_within_limit(temp_range.max):
            return False, f"CPP out of range.  Max temperature was {temp_range.max}"
        return True, f"CPP Met.  Max temperature was {temp_range.max}"


class PhRange(ProcessCheck):

    def check_is_successful(self):
        # Similar to TemperatureRange - we don't have a requirement to check for PH range
        # We're just reporting
        ph_range = self._batch_record.get_reading_range("pH")
        return True, f"pH ranged from {ph_range.min} to {ph_range.max}"


class PressureRange(ProcessCheck):

    def check_is_successful(self):
        pressure_range = self._batch_record.get_reading_range("pressure")
        return True, f"Pressure ranged from {pressure_range.min} to {pressure_range.max}"


class PressureMaximum(ProcessCheck):

    def check_is_successful(self):
        pressure_range = self._batch_record.get_reading_range("pressure")

        if not self.is_within_limit(pressure_range.max):
            return False, f"CPP out of range.  Pressure got too high: {pressure_range.max}"
        return True, f"CPP Met.  Max pressure was {pressure_range.max}"


class RunTime(ProcessCheck):
    # TODO: The spec here says "•   Total time for the process "
    # Find out if this means from the time you start filling until the time the reactor is empty
    # or if it means from the time you close the input valve to the time you open the output valve.

    # The implementation below assumes the latter, but it can be easily changed

    def check_is_successful(self):
        duration = self._batch_record.filter_by_step_name("run").process_duration()
        return True, f"Batch reacted for {duration}s"
