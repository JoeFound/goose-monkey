from typing import Callable

from serpentarium import SingleUsePlugin

from common.event_queue import IAgentEventPublisher
from common.types import AgentID

from .i_plugin_factory import IPluginFactory


class CredentialsCollectorPluginFactory(IPluginFactory):
    def __init__(
        self,
        agent_id: AgentID,
        agent_event_publisher: IAgentEventPublisher,
        create_plugin: Callable[..., SingleUsePlugin],
    ):
        self._agent_id = agent_id
        self._agent_event_publisher = agent_event_publisher
        self._create_plugin = create_plugin

    def create(self, plugin_name: str) -> SingleUsePlugin:
        return self._create_plugin(
            plugin_name=plugin_name,
            agent_id=self._agent_id,
            agent_event_publisher=self._agent_event_publisher,
        )
