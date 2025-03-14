import random
from pathlib import PurePosixPath

import pytest
from semver import VersionInfo

from common.agent_plugins import AgentPluginMetadata, AgentPluginRepositoryIndex, AgentPluginType
from common.agent_plugins.agent_plugin_repository_index import (  # type: ignore[attr-defined]
    DEVELOPMENT,
)

PAYLOAD_PLUGIN_NAME = "awesome_payload"


def get_plugin_metadata_with_given_version(version: str) -> AgentPluginMetadata:
    return AgentPluginMetadata(
        name=PAYLOAD_PLUGIN_NAME,
        type_=AgentPluginType.PAYLOAD,
        resource_path=PurePosixPath("/tmp"),
        sha256="7ac0f5c62a9bcb81af3e9d67a764d7bbd3cce9af7cd26c211f136400ebe703c4",
        description="an awesome payload plugin",
        version=version,
        safe=True,
    )


PLUGIN_VERSION_1_0_0 = get_plugin_metadata_with_given_version("1.0.0")
PLUGIN_VERSION_1_0_1 = get_plugin_metadata_with_given_version("1.0.1")
PLUGIN_VERSION_1_2_0 = get_plugin_metadata_with_given_version("1.2.0")
PLUGIN_VERSION_1_2_3 = get_plugin_metadata_with_given_version("1.2.3")
PLUGIN_VERSION_2_0_0 = get_plugin_metadata_with_given_version("2.0.0")
PLUGIN_VERSION_3_0_1 = get_plugin_metadata_with_given_version("3.0.1")
PLUGIN_VERSION_3_0_1_SERIALIZED = {
    "name": PAYLOAD_PLUGIN_NAME,
    "type_": AgentPluginType.PAYLOAD.value,
    "resource_path": "/tmp",
    "sha256": "7ac0f5c62a9bcb81af3e9d67a764d7bbd3cce9af7cd26c211f136400ebe703c4",
    "description": "an awesome payload plugin",
    "version": "3.0.1",
    "safe": True,
}

SORTED_PLUGIN_VERSIONS = [
    PLUGIN_VERSION_1_0_0,
    PLUGIN_VERSION_1_0_1,
    PLUGIN_VERSION_1_2_0,
    PLUGIN_VERSION_1_2_3,
    PLUGIN_VERSION_2_0_0,
    PLUGIN_VERSION_3_0_1,
]

REPOSITORY_INDEX_PLUGINS = {AgentPluginType.PAYLOAD: {PAYLOAD_PLUGIN_NAME: [PLUGIN_VERSION_3_0_1]}}
REPOSITORY_INDEX_PLUGINS_SERIALIZED = {
    AgentPluginType.PAYLOAD.value: {PAYLOAD_PLUGIN_NAME: [PLUGIN_VERSION_3_0_1_SERIALIZED]}
}


def get_repository_index_with_given_version(version: str) -> AgentPluginRepositoryIndex:
    return AgentPluginRepositoryIndex(
        timestamp=123, compatible_infection_monkey_version=version, plugins=REPOSITORY_INDEX_PLUGINS
    )


REPOSITORY_INDEX_VERSION_DEVELOPMENT = get_repository_index_with_given_version(DEVELOPMENT)
REPOSITORY_INDEX_VERSION_DEVELOPMENT_SERIALIZED = {
    "timestamp": 123,
    "compatible_infection_monkey_version": DEVELOPMENT,
    "plugins": REPOSITORY_INDEX_PLUGINS_SERIALIZED,
}


REPOSITORY_INDEX_VERSION_OBJECT = get_repository_index_with_given_version(VersionInfo(7, 8, 9))
REPOSITORY_INDEX_VERSION_DICT = get_repository_index_with_given_version("7.8.9")
REPOSITORY_INDEX_VERSION_SERIALIZED = {
    "timestamp": 123,
    "compatible_infection_monkey_version": "7.8.9",
    "plugins": REPOSITORY_INDEX_PLUGINS_SERIALIZED,
}


@pytest.mark.parametrize(
    "object_,expected_serialization",
    [
        (REPOSITORY_INDEX_VERSION_DEVELOPMENT, REPOSITORY_INDEX_VERSION_DEVELOPMENT_SERIALIZED),
        (REPOSITORY_INDEX_VERSION_DICT, REPOSITORY_INDEX_VERSION_SERIALIZED),
        (REPOSITORY_INDEX_VERSION_OBJECT, REPOSITORY_INDEX_VERSION_SERIALIZED),
    ],
)
def test_agent_plugin_repository_index_serialization(object_, expected_serialization):
    assert object_.dict(simplify=True) == expected_serialization


@pytest.mark.parametrize(
    "expected_object,serialized",
    [
        (REPOSITORY_INDEX_VERSION_DEVELOPMENT, REPOSITORY_INDEX_VERSION_DEVELOPMENT_SERIALIZED),
        (REPOSITORY_INDEX_VERSION_DICT, REPOSITORY_INDEX_VERSION_SERIALIZED),
        (REPOSITORY_INDEX_VERSION_OBJECT, REPOSITORY_INDEX_VERSION_SERIALIZED),
    ],
)
def test_agent_plugin_repository_index_deserialization(expected_object, serialized):
    assert AgentPluginRepositoryIndex(**serialized) == expected_object


def test_plugins_sorted_by_version():
    UNSORTED_PLUGIN_VERSIONS = SORTED_PLUGIN_VERSIONS.copy()
    random.shuffle(UNSORTED_PLUGIN_VERSIONS)  # noqa: DUO102

    assert UNSORTED_PLUGIN_VERSIONS != SORTED_PLUGIN_VERSIONS

    repository_index = AgentPluginRepositoryIndex(
        compatible_infection_monkey_version="development",
        plugins={
            AgentPluginType.PAYLOAD.value: {PAYLOAD_PLUGIN_NAME: UNSORTED_PLUGIN_VERSIONS},
            AgentPluginType.EXPLOITER.value: {},
            AgentPluginType.CREDENTIALS_COLLECTOR.value: {
                PAYLOAD_PLUGIN_NAME: [PLUGIN_VERSION_1_0_0]
            },
        },
    )

    assert repository_index.plugins == {
        AgentPluginType.PAYLOAD.value: {PAYLOAD_PLUGIN_NAME: SORTED_PLUGIN_VERSIONS},
        AgentPluginType.EXPLOITER.value: {},
        AgentPluginType.CREDENTIALS_COLLECTOR.value: {PAYLOAD_PLUGIN_NAME: [PLUGIN_VERSION_1_0_0]},
    }
