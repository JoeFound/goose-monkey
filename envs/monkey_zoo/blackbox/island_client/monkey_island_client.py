import json
import logging
import time
from http import HTTPStatus
from typing import List, Mapping, Optional, Sequence

from common import OperatingSystem
from common.credentials import Credentials
from common.types import AgentID, MachineID
from envs.monkey_zoo.blackbox.island_client.i_monkey_island_requests import IMonkeyIslandRequests
from envs.monkey_zoo.blackbox.test_configurations.test_configuration import TestConfiguration
from monkey_island.cc.models import Agent, Machine, TerminateAllAgents

SLEEP_BETWEEN_REQUESTS_SECONDS = 0.5
GET_AGENTS_ENDPOINT = "api/agents"
GET_LOG_ENDPOINT = "api/agent-logs"
ISLAND_LOG_ENDPOINT = "api/island/log"
GET_MACHINES_ENDPOINT = "api/machines"
GET_AGENT_EVENTS_ENDPOINT = "api/agent-events"
LOGOUT_ENDPOINT = "api/logout"
GET_AGENT_OTP_ENDPOINT = "/api/agent-otp"

LOGGER = logging.getLogger(__name__)


def avoid_race_condition(func):
    time.sleep(SLEEP_BETWEEN_REQUESTS_SECONDS)
    return func


class MonkeyIslandClient(object):
    def __init__(self, requests: IMonkeyIslandRequests):
        self.requests = requests

    def get_api_status(self):
        return self.requests.get("api")

    @avoid_race_condition
    def set_masque(self, masque):
        masque = b"" if masque is None else masque
        for operating_system in [operating_system.name for operating_system in OperatingSystem]:
            if self.requests.put(f"api/agent-binaries/{operating_system}/masque", data=masque).ok:
                formatted_masque = masque if len(masque) <= 64 else (masque[:64] + b"...")
                LOGGER.info(f'Setting {operating_system} masque to "{formatted_masque}"')
            else:
                LOGGER.error(f"Failed to set {operating_system} masque")
                assert False

    def get_agent_binary(self, operating_system: OperatingSystem) -> bytes:
        response = self.requests.get(f"api/agent-binaries/{operating_system.name}")
        return response.content

    def get_propagation_credentials(self) -> Sequence[Credentials]:
        response = self.requests.get("api/propagation-credentials")
        return [Credentials(**credentials) for credentials in response.json()]

    def get_stolen_credentials(self) -> Sequence[Credentials]:
        response = self.requests.get("api/propagation-credentials/stolen-credentials")
        return [Credentials(**credentials) for credentials in response.json()]

    @avoid_race_condition
    def import_config(self, test_configuration: TestConfiguration):
        self._import_config(test_configuration)
        self._import_credentials(test_configuration.propagation_credentials)

    @avoid_race_condition
    def _import_config(self, test_configuration: TestConfiguration):
        response = self.requests.put_json(
            "api/agent-configuration",
            json=test_configuration.agent_configuration.dict(simplify=True),
        )
        if response.ok:
            LOGGER.info("Configuration is imported.")
        else:
            LOGGER.error(f"Failed to import config: {response}")
            assert False

    @avoid_race_condition
    def _import_credentials(self, propagation_credentials: List[Credentials]):
        serialized_propagation_credentials = [
            credentials.dict(simplify=True) for credentials in propagation_credentials
        ]
        response = self.requests.put_json(
            "/api/propagation-credentials/configured-credentials",
            json=serialized_propagation_credentials,
        )
        if response.ok:
            LOGGER.info("Credentials are imported.")
        else:
            LOGGER.error(f"Failed to import credentials: {response}")
            assert False

    @avoid_race_condition
    def run_monkey_local(self):
        response = self.requests.post_json("api/local-monkey", json={"action": "run"})
        if MonkeyIslandClient.monkey_ran_successfully(response):
            LOGGER.info("Running the monkey.")
        else:
            LOGGER.error("Failed to run the monkey.")
            assert False

    @staticmethod
    def monkey_ran_successfully(response):
        return response.ok and json.loads(response.content)["is_running"]

    @avoid_race_condition
    def kill_all_monkeys(self):
        # TODO change this request, because monkey-control resource got removed
        response = self.requests.post_json(
            "api/agent-signals/terminate-all-agents",
            json=TerminateAllAgents(timestamp=time.time()).dict(simplify=True),
        )
        if response.ok:
            LOGGER.info("Killing all monkeys after the test.")
        else:
            LOGGER.error("Failed to kill all monkeys.")
            LOGGER.error(response.status_code)
            LOGGER.error(response.content)
            assert False

    @avoid_race_condition
    def reset_island(self):
        self._reset_agent_configuration()
        self._reset_simulation_data()
        self._reset_credentials()
        self.set_masque(b"")

    def _reset_agent_configuration(self):
        if self.requests.post("api/reset-agent-configuration", data=None).ok:
            LOGGER.info("Resetting agent-configuration after the test.")
        else:
            LOGGER.error("Failed to reset agent configuration.")
            assert False

    def _reset_simulation_data(self):
        if self.requests.post("api/clear-simulation-data", data=None).ok:
            LOGGER.info("Clearing simulation data.")
        else:
            LOGGER.error("Failed to clear simulation data")
            assert False

    def _reset_credentials(self):
        if self.requests.put_json("api/propagation-credentials/configured-credentials", json=[]).ok:
            LOGGER.info("Resseting configured credentials after the test.")
        else:
            LOGGER.error("Failed to reset configured credentials")
            assert False

    def get_agents(self) -> Sequence[Agent]:
        response = self.requests.get(GET_AGENTS_ENDPOINT)

        return [Agent(**a) for a in response.json()]

    def get_machines(self) -> Mapping[MachineID, Machine]:
        response = self.requests.get(GET_MACHINES_ENDPOINT)
        machines = (Machine(**m) for m in response.json())

        return {m.id: m for m in machines}

    def get_agent_log(self, agent_id: AgentID) -> Optional[str]:
        response = self.requests.get(f"{GET_LOG_ENDPOINT}/{agent_id}")

        if response.status_code == HTTPStatus.NOT_FOUND:
            LOGGER.error(f"No log found for agent: {agent_id}")
            return None
        else:
            response.raise_for_status()

        return response.json()

    def get_island_log(self):
        response = self.requests.get(f"{ISLAND_LOG_ENDPOINT}")

        response.raise_for_status()

        return response.json()

    def get_agent_events(self):
        response = self.requests.get(GET_AGENT_EVENTS_ENDPOINT)

        return response.json()

    def is_all_monkeys_dead(self):
        agents = self.get_agents()
        return all((a.stop_time is not None for a in agents))

    def register(self):
        try:
            self.requests.register()
            LOGGER.info("Successfully registered a user with the Island.")
        except Exception:
            LOGGER.error("Failed to register a user with the Island.")

    def login(self):
        try:
            self.requests.login()
            LOGGER.info("Logged into the Island.")
        except Exception:
            LOGGER.error("Failed to log into the Island.")
            assert False

    def logout(self):
        if self.requests.post(LOGOUT_ENDPOINT, data=None).ok:
            LOGGER.info("Logged out of the Island.")
        else:
            LOGGER.error("Failed to log out of the Island.")
            assert False

    def get_agent_otp(self):
        response = self.requests.get(GET_AGENT_OTP_ENDPOINT)
        return response.json()
