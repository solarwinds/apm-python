# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
from __future__ import annotations

import logging
import os
import re
from contextlib import suppress

from opentelemetry.sdk.resources import Resource, ResourceDetector
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)

NAMESPACE_ENV = "SW_K8S_POD_NAMESPACE"
UID_ENV = "SW_K8S_POD_UID"
NAME_ENV = "SW_K8S_POD_NAME"

NAMESPACE_FILE = (
    "C:\\var\\run\\secrets\\kubernetes.io\\serviceaccount\\namespace"
    if os.name == "nt"
    else "/run/secrets/kubernetes.io/serviceaccount/namespace"
)

MOUNTINFO_FILE = "/proc/self/mountinfo"
UID_REGEX = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}", re.I)


def _pod_name() -> str:
    env = os.getenv(NAME_ENV)
    if env:
        logger.debug("read pod name from env")
        return env

    return os.uname().nodename


def _pod_uid(mount_info: str) -> str | None:
    env = os.getenv(UID_ENV)
    if env:
        logger.debug("read pod uid from env")
        return env

    if os.name == "nt":
        logger.debug("can't read pod uid on windows")
        return None

    with suppress(Exception):
        with open(mount_info, "r", encoding="utf-8") as file:
            for line in file:
                fields = line.split(" ")
                if len(fields) < 10:
                    continue

                identity, parent_id, _, root = fields[:4]
                if not identity.isdigit() or not parent_id.isdigit():
                    continue

                if "kube" not in root:
                    continue

                match = UID_REGEX.search(root)
                if match:
                    return match.group(0)

    logger.debug("can't read pod uid")
    return None


def _pod_namespace(namespace: str) -> str | None:
    env = os.getenv(NAMESPACE_ENV)
    if env:
        logger.debug("read pod namespace from env")
        return env

    with suppress(Exception):
        with open(namespace, "r", encoding="utf-8") as file:
            logger.debug("read pod namespace from file")
            return file.read().strip()

    logger.debug("can't read pod namespace")
    return None


class K8sResourceDetector(ResourceDetector):
    """Detects attribute values only available when the app is running on k8s
    and returns them in a Resource.
    """

    def __init__(
        self, namespace: str = NAMESPACE_FILE, mountinfo: str = MOUNTINFO_FILE
    ):
        super().__init__()
        self._namespace = namespace
        self._mountinfo = mountinfo

    def detect(self) -> Resource:
        attributes = {}

        namespace = _pod_namespace(self._namespace)
        if namespace:
            attributes[ResourceAttributes.K8S_NAMESPACE_NAME] = namespace
        else:
            return Resource.get_empty()

        uid = _pod_uid(self._mountinfo)
        if uid:
            attributes[ResourceAttributes.K8S_POD_UID] = uid

        name = _pod_name()
        if name:
            attributes[ResourceAttributes.K8S_POD_NAME] = name

        return Resource(attributes)
