# © 2025 SolarWinds Worldwide, LLC. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.


import os
import tempfile
import uuid
import random
import string
from contextlib import suppress

import pytest

from opentelemetry.semconv.resource import ResourceAttributes

from solarwinds_apm.k8s import K8sResourceDetector

NAMESPACE_FILE = os.path.join(tempfile.gettempdir(), "solarwinds-apm-k8s-namespace")
MOUNTINFO_FILE = os.path.join(tempfile.gettempdir(), "solarwinds-apm-mountinfo")

ENV_NAMESPACE = "".join(random.choices(string.hexdigits, k=16))
FILE_NAMESPACE = "".join(random.choices(string.hexdigits, k=16))

ENV_UID = str(uuid.uuid4())
FILE_UID = str(uuid.uuid4())

ENV_NAME = "".join(random.choices(string.hexdigits, k=8))


@pytest.fixture(autouse=True)
def cleanup():
    yield
    with suppress(FileNotFoundError):
        os.remove(NAMESPACE_FILE)
        os.remove(MOUNTINFO_FILE)


def file_namespace():
    with open(NAMESPACE_FILE, "w") as f:
        f.write(f"{FILE_NAMESPACE}\n")


def file_uid():
    with open(MOUNTINFO_FILE, "w") as f:
        f.write(f"""
757 605 0:139 / / rw,relatime master:180 - overlay overlay rw,context="system_u:object_r:data_t:s0:c171,c852",lowerdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/25/fs,upperdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/26/fs,workdir=/var/lib/containerd/io.containerd.snapshotter.v1.overlayfs/snapshots/26/work
758 757 0:143 / /proc rw,nosuid,nodev,noexec,relatime - proc proc rw
760 757 0:145 / /dev rw,nosuid - tmpfs tmpfs rw,context="system_u:object_r:data_t:s0:c171,c852",size=65536k,mode=755
762 760 0:147 / /dev/pts rw,nosuid,noexec,relatime - devpts devpts rw,context="system_u:object_r:data_t:s0:c171,c852",gid=5,mode=620,ptmxmode=666
764 760 0:105 / /dev/mqueue rw,nosuid,nodev,noexec,relatime - mqueue mqueue rw,seclabel
765 757 0:111 / /sys ro,nosuid,nodev,noexec,relatime - sysfs sysfs ro,seclabel
767 765 0:25 / /sys/fs/cgroup ro,nosuid,nodev,noexec,relatime - cgroup2 cgroup rw,seclabel
769 757 259:16 /var/lib/kubelet/pods/${FILE_UID}/volumes/kubernetes.io~empty-dir/html /html rw,nosuid,nodev,noatime - ext4 /dev/nvme1n1p1 rw,seclabel
772 757 259:16 /var/lib/kubelet/pods/${FILE_UID}/etc-hosts /etc/hosts rw,nosuid,nodev,noatime - ext4 /dev/nvme1n1p1 rw,seclabel
773 760 259:16 /var/lib/kubelet/pods/${FILE_UID}/containers/2nd/7aa42719 /dev/termination-log rw,nosuid,nodev,noatime - ext4 /dev/nvme1n1p1 rw,seclabel
774 757 259:16 /var/lib/containerd/io.containerd.grpc.v1.cri/sandboxes/bd9a3e80e86b8ffbe97ed67b484bd132dcc7b99106ce6ab58e1118287a5b1a60/hostname /etc/hostname rw,nosuid,nodev,noatime - ext4 /dev/nvme1n1p1 rw,seclabel
776 757 259:16 /var/lib/containerd/io.containerd.grpc.v1.cri/sandboxes/bd9a3e80e86b8ffbe97ed67b484bd132dcc7b99106ce6ab58e1118287a5b1a60/resolv.conf /etc/resolv.conf rw,nosuid,nodev,noatime - ext4 /dev/nvme1n1p1 rw,seclabel
778 760 0:100 / /dev/shm rw,nosuid,nodev,noexec,relatime - tmpfs shm rw,seclabel,size=65536k
781 757 0:98 / /run/secrets/kubernetes.io/serviceaccount ro,relatime - tmpfs tmpfs rw,seclabel,size=3380568k
606 758 0:143 /bus /proc/bus ro,nosuid,nodev,noexec,relatime - proc proc rw
607 758 0:143 /fs /proc/fs ro,nosuid,nodev,noexec,relatime - proc proc rw
608 758 0:143 /irq /proc/irq ro,nosuid,nodev,noexec,relatime - proc proc rw
609 758 0:143 /sys /proc/sys ro,nosuid,nodev,noexec,relatime - proc proc rw
610 758 0:143 /sysrq-trigger /proc/sysrq-trigger ro,nosuid,nodev,noexec,relatime - proc proc rw
621 758 0:149 / /proc/acpi ro,relatime - tmpfs tmpfs ro,context="system_u:object_r:data_t:s0:c171,c852"
622 758 0:145 /null /proc/kcore rw,nosuid - tmpfs tmpfs rw,context="system_u:object_r:data_t:s0:c171,c852",size=65536k,mode=755
624 758 0:145 /null /proc/keys rw,nosuid - tmpfs tmpfs rw,context="system_u:object_r:data_t:s0:c171,c852",size=65536k,mode=755
625 758 0:145 /null /proc/latency_stats rw,nosuid - tmpfs tmpfs rw,context="system_u:object_r:data_t:s0:c171,c852",size=65536k,mode=755
626 758 0:145 /null /proc/timer_list rw,nosuid - tmpfs tmpfs rw,context="system_u:object_r:data_t:s0:c171,c852",size=65536k,mode=755
627 758 0:150 / /proc/scsi ro,relatime - tmpfs tmpfs ro,context="system_u:object_r:data_t:s0:c171,c852"
628 765 0:151 / /sys/firmware ro,relatime - tmpfs tmpfs ro,context="system_u:object_r:data_t:s0:c171,c852"
    """)


def test_detects_attributes_from_env(mocker):
    mocker.patch.dict(
        os.environ,
        {
            "SW_K8S_POD_NAMESPACE": ENV_NAMESPACE,
            "SW_K8S_POD_UID": ENV_UID,
            "SW_K8S_POD_NAME": ENV_NAME,
        },
    )

    k8s_detector = K8sResourceDetector(NAMESPACE_FILE, MOUNTINFO_FILE)
    resource = k8s_detector.detect()

    assert resource.attributes == {
        ResourceAttributes.K8S_NAMESPACE_NAME: ENV_NAMESPACE,
        ResourceAttributes.K8S_POD_UID: ENV_UID,
        ResourceAttributes.K8S_POD_NAME: ENV_NAME,
    }


def test_detects_attributes_from_files():
    file_namespace()
    file_uid()

    k8s_detector = K8sResourceDetector(NAMESPACE_FILE, MOUNTINFO_FILE)
    resource = k8s_detector.detect()

    expected_attributes = {
        ResourceAttributes.K8S_NAMESPACE_NAME: FILE_NAMESPACE,
        ResourceAttributes.K8S_POD_NAME: os.uname().nodename,
    }
    if os.name != "nt":
        expected_attributes[ResourceAttributes.K8S_POD_UID] = FILE_UID

    assert resource.attributes == expected_attributes


def test_prefers_env_over_files(mocker):
    mocker.patch.dict(
        os.environ,
        {
            "SW_K8S_POD_NAMESPACE": ENV_NAMESPACE,
            "SW_K8S_POD_UID": ENV_UID,
            "SW_K8S_POD_NAME": ENV_NAME,
        },
    )
    file_namespace()
    file_uid()

    k8s_detector = K8sResourceDetector(NAMESPACE_FILE, MOUNTINFO_FILE)
    resource = k8s_detector.detect()

    assert resource.attributes == {
        ResourceAttributes.K8S_NAMESPACE_NAME: ENV_NAMESPACE,
        ResourceAttributes.K8S_POD_UID: ENV_UID,
        ResourceAttributes.K8S_POD_NAME: ENV_NAME,
    }


def test_doesnt_detect_uid_or_name_without_namespace(mocker):
    mocker.patch.dict(
        os.environ,
        {
            "SW_K8S_POD_UID": ENV_UID,
            "SW_K8S_POD_NAME": ENV_NAME,
        },
    )
    file_uid()

    k8s_detector = K8sResourceDetector(NAMESPACE_FILE, MOUNTINFO_FILE)
    resource = k8s_detector.detect()

    assert resource.attributes == {}
