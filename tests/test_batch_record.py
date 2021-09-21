from bioreactor_client.batch_record import BatchRecord


def test_process_step_names():
    dut = BatchRecord()
    dut.record_reactor_status("foo", {"a": 1, "b": 2, "c": 3})
    dut.record_reactor_status("foo", {"a": 1, "b": 2, "c": 3})
    dut.record_reactor_status("foo", {"a": 1, "b": 2, "c": 3})
    dut.record_reactor_status("bar", {"a": 1, "b": 2, "c": 3})
    dut.record_reactor_status("baz", {"a": 1, "b": 2, "c": 3})
    dut.record_reactor_status("baz", {"a": 1, "b": 2, "c": 3})

    # Make sure all our fake process step names are recognized
    assert "foo" in dut.get_process_steps()
    assert "bar" in dut.get_process_steps()
    assert "baz" in dut.get_process_steps()

    # Make sure there are no extra process step names
    assert len(dut.get_process_steps()) == 3

    foo_only = dut.filter_by_step_name("foo")
    assert "foo" in foo_only.get_process_steps()
    assert "bar" not in foo_only.get_process_steps()
    assert "baz" not in foo_only.get_process_steps()

# Again, tests are deliberately incomplete here.
# We are missing a robust set of test cases for BatchRecord,
# as well as test cases for the ProcessCheck validators
# that ensure our various process parameters remained within the
# acceptable range
