import requests


def get_reactor(service_host="http://mini-mes.resilience.com"):
    response = requests.get(f"{service_host}/bioreactor/0")
    return ReactorApiClient(service_host, response.json()["id"])


class ReactorApiClient:
    """A python wrapper for the bioreactor REST API."""

    def __init__(self, service_host, reactor_id):
        self._service_host = service_host
        self._reactor_id = reactor_id
        self.input_valve = ValveApiClient(service_host, reactor_id, "input-valve")
        self.output_valve = ValveApiClient(service_host, reactor_id, "output-valve")

    def get_reactor_status(self):
        response = requests.get(f"{self._service_host}/bioreactor/{self._reactor_id}")
        return response.json()


class ValveApiClient:
    """A python wrapper for the input-valve and output-valve REST APIs."""

    def __init__(self, service_host, reactor_id, valve_name):
        if valve_name not in ["input-valve", "output-valve"]:
            raise ValueError(f"Unrecognized valve name {valve_name}")

        self._api_url = f"{service_host}/bioreactor/{reactor_id}/{valve_name}"

    def get_valve_state(self):
        """Get the current state of the valve.

        Returns
        -------
        String: The state of the valve.
            Either "open" or "closed"
        """

        response = requests.get(self._api_url)
        return response.json()["state"]

    def open_valve(self):
        """Open this valve."""
        response = requests.put(self._api_url, json={"state": "open"})
        response.raise_for_status()
        # TODO: A better design might be to have a specific exception here that the client can
        # catch.
        # This will alert the client that something is wrong, but it will be hard for the
        # client to do anything other than barf up a stack trace.
        # One would hope this would pop up in a server-side log too to alert the provider of the
        # API that one of their valves isn't working correctly.
        assert response.json()["state"] == "open"

    def close_valve(self):
        """Close this valve."""
        response = requests.put(self._api_url, json={"state": "closed"})
        response.raise_for_status()
        assert response.json()["state"] == "closed"
