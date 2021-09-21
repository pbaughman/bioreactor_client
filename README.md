# Resilliance Bioreactor Client

This python package provides a command-line client to Resilliance's bioreactor simulator API.

Example usage:

```
$ python3 -m pip install <path_to_bioreactor_client>
$ run_reactor
```

A successful run looks something like:

```
$ run_reactor
Starting reaction in reactor 81990
T=0.67, Process State=fill
T=35.21, Process State=run
T=113.8, Process State=empty
T=148.72, Process State=done


---------- Final Report ----------
Process ran until the end
Max level reached during fill stage was 68.714
CPP Met. Fill level during run was 69.07% to 69.07%
Temperature ranged from 25.0 to 79.2807316
CPP Met.  Max temperature was 79.2807316
pH ranged from 7 to 7
Pressure ranged from 113 to 113
CPP Met.  Max pressure was 113
Batch took 0:01:18.063910s
The overall status of this batch is: SUCCESS
```

You can also run unit tests very easily.  Ensure `tox` is installed

```
$ python3 -m pip install tox  # If tox isn't installed
$ cd <path_to_bioreactor_client>
$ tox
```

A successful run looks something like:

```
========================================== test session starts ==========================================
platform linux -- Python 3.7.3, pytest-6.2.5, py-1.10.0, pluggy-1.0.0 -- /home/pi/bioreactor_client/.tox/
py37/bin/python
cachedir: .tox/py37/.pytest_cache
rootdir: /home/pi/bioreactor_client
collected 8 items

tests/test_empty_reactor_state.py::test_emptying PASSED                                           [ 12%]
tests/test_fill_state.py::test_filling PASSED                                                     [ 25%]
tests/test_fill_state.py::test_overfilled PASSED                                                  [ 37%]
tests/test_fill_state.py::test_filled_correctly PASSED                                            [ 50%]
tests/test_run_reactor_state.py::test_running PASSED                                              [ 62%]
tests/test_start_state.py::test_successful_start PASSED                                           [ 75%]
tests/test_start_state.py::test_start_with_input_open PASSED                                      [ 87%]
tests/test_start_state.py::test_start_with_output_open PASSED                                     [100%]

=========================================== 8 passed in 0.27s ===========================================
```
