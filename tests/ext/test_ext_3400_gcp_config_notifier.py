# -----------------------------------------------------------------------------
# Copyright (c) 2026, Oracle and/or its affiliates.
#
# This software is dual-licensed to you under the Universal Permissive License
# (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl and Apache License
# 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose
# either license.
#
# If you elect to accept the software under the Apache License, Version 2.0,
# the following applies:
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------

"""
E3400 - Module for testing GCP config cache notifications with real resources.

These tests are part of the extended test suite and only run when
run_long_tests is enabled and when the following entries are also set:

    gcp_project_id
        GCP project that owns the bucket, secrets and subscriptions.
    gcp_bucket_name
        Bucket with a Cloud Storage notification that publishes
        OBJECT_FINALIZE and OBJECT_DELETE events to the topic of the
        subscription below, using the JSON_API_V1 payload format.
    gcp_object_prefix
        Prefix used to create a unique temporary config object.
    gcp_gcs_pubsub_subscription_name
        Pull subscription for the bucket notifications, in the form
        projects/<project>/subscriptions/<subscription>.
    gcp_secret_name
        Base name used to create unique temporary secrets.
    gcp_secretmanager_pubsub_topic_name
        Topic that Secret Manager publishes secret events to.
    gcp_secretmanager_pubsub_subscription_name
        Pull subscription for that topic.

Each subscription must be dedicated to these tests. Authentication uses
Application Default Credentials (ADC). Notification tests require the
google-cloud-pubsub package. Do not run concurrent test processes against
the same subscription.
The test credentials also require secretmanager.secrets.update permission.
E3408 also requires pubsub.subscriptions.get, pubsub.subscriptions.create,
pubsub.subscriptions.delete, and pubsub.topics.attachSubscription permissions
for a temporary subscription.
"""

import json
import threading
import time
import uuid

import oracledb
import pytest

plugin = pytest.importorskip("oracledb.plugins.gcp_config_provider")


class GcpNotifierConfig:
    """
    Manages the real Cloud Storage resources required by the notifier test.
    """

    def __init__(self, test_env, extended_config):
        self.test_env = test_env
        self.project_id = extended_config.get_str_value("gcp_project_id")
        self.bucket_name = extended_config.get_str_value("gcp_bucket_name")
        self.object_prefix = extended_config.get_str_value("gcp_object_prefix")
        self.subscription_name = extended_config.get_str_value(
            "gcp_gcs_pubsub_subscription_name"
        )
        if not self.project_id:
            pytest.skip("GCP project ID is not configured")
        if not self.bucket_name:
            pytest.skip("GCP bucket name is not configured")
        if not self.object_prefix:
            pytest.skip("GCP object prefix is not configured")
        if not self.subscription_name:
            pytest.skip("GCP Pub/Sub subscription name is not configured")

        run_id = uuid.uuid4().hex[:16]
        self.blob = None
        self.listener_thread = None
        self.object_name = f"{self.object_prefix}_{run_id}_notifier.json"
        self.dsn = (
            "config-gcpstorage://"
            f"project={self.project_id};"
            f"bucket={self.bucket_name};"
            f"object={self.object_name}"
            f"?subscriptionname={self.subscription_name}"
        )

    def cleanup(self):
        try:
            if self.blob is not None:
                self.delete_config()
        finally:
            if self.listener_thread is not None:
                self.listener_thread.join(timeout=10)

    def delete_config(self):
        try:
            self.blob.delete()
        except self.not_found_error:
            pass

    def setup(self, client):
        from google.api_core.exceptions import NotFound

        self.not_found_error = NotFound
        bucket = client.lookup_bucket(self.bucket_name)
        if bucket is None:
            pytest.skip(f"GCP bucket {self.bucket_name} not found")

        self.blob = bucket.blob(self.object_name)

    def upload_config(self, stmtcachesize, time_to_live=3600):
        config = dict(
            connect_descriptor=self.test_env.connect_string,
            config_time_to_live=time_to_live,
            pyo=dict(stmtcachesize=stmtcachesize),
        )
        self.blob.upload_from_string(
            json.dumps(config),
            content_type="application/json",
        )


class GcpSecretManagerNotifierConfig:
    """
    Manages the real Secret Manager resources required by the notifier test.
    """

    def __init__(self, test_env, extended_config):
        self.test_env = test_env
        self.project_id = extended_config.get_str_value("gcp_project_id")
        self.secret_name = extended_config.get_str_value("gcp_secret_name")
        self.topic_name = extended_config.get_str_value(
            "gcp_secretmanager_pubsub_topic_name"
        )
        self.subscription_name = extended_config.get_str_value(
            "gcp_secretmanager_pubsub_subscription_name"
        )
        if not self.project_id:
            pytest.skip("GCP project ID is not configured")
        if not self.secret_name:
            pytest.skip("GCP Secret Manager secret name is not configured")
        if not self.topic_name:
            pytest.skip("GCP Secret Manager Pub/Sub topic is not configured")
        if not self.subscription_name:
            pytest.skip(
                "GCP Secret Manager Pub/Sub subscription is not configured"
            )

        run_id = uuid.uuid4().hex[:16]
        self.secret_id = f"{self.secret_name}-{run_id}-notifier"
        self.secret_deleted = True

    def add_config_version(self, stmtcachesize, time_to_live=3600):
        config = dict(
            connect_descriptor=self.test_env.connect_string,
            config_time_to_live=time_to_live,
            config_time_to_live_grace_period=0,
            pyo=dict(stmtcachesize=stmtcachesize),
        )
        response = self.client.add_secret_version(
            request={
                "parent": self.secret_path,
                "payload": {"data": json.dumps(config).encode()},
            }
        )
        return response.name

    def delete_secret(self):
        if self.secret_deleted:
            return
        try:
            self.client.delete_secret(request={"name": self.secret_path})
        except self.not_found_error:
            pass
        self.secret_deleted = True

    def enable_notifications(self):
        self.client.update_secret(
            request={
                "secret": {
                    "name": self.secret_path,
                    "topics": [{"name": self.topic_name}],
                },
                "update_mask": {"paths": ["topics"]},
            }
        )

    def get_dsn(self, version_name=None):
        resource_name = version_name or f"{self.secret_path}/versions/latest"
        return (
            f"config-gcpsecretmanager://{resource_name}"
            f"?subscriptionname={self.subscription_name}"
        )

    def setup(self, client):
        from google.api_core.exceptions import NotFound

        self.not_found_error = NotFound
        self.client = client
        self.secret_path = self.client.secret_path(
            self.project_id,
            self.secret_id,
        )
        self.client.create_secret(
            request={
                "parent": f"projects/{self.project_id}",
                "secret_id": self.secret_id,
                "secret": {
                    "replication": {"automatic": {}},
                },
            }
        )
        self.secret_deleted = False


def drain_subscription(subscription_name):
    """
    Acknowledges messages left on the subscription by earlier runs.
    """
    from google.api_core.exceptions import DeadlineExceeded
    from google.cloud import pubsub_v1

    request_timeout = 5
    with pubsub_v1.SubscriberClient() as client:
        deadline = time.monotonic() + 10
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            try:
                response = client.pull(
                    request=dict(
                        subscription=subscription_name,
                        max_messages=100,
                    ),
                    timeout=min(request_timeout, remaining),
                    retry=None,
                )
            except DeadlineExceeded:
                return

            if not response.received_messages:
                return

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            client.acknowledge(
                request=dict(
                    subscription=subscription_name,
                    ack_ids=[
                        message.ack_id
                        for message in response.received_messages
                    ],
                ),
                timeout=min(request_timeout, remaining),
                retry=None,
            )


def get_stmtcachesize(dsn):
    params = oracledb.ConnectParams()
    params.parse_connect_string(dsn)
    return params.stmtcachesize


def wait_for_removed_configs(*dsns):
    """
    Waits for all specified configurations to be hard-invalidated.
    """
    remaining_dsns = set(dsns)
    deadline = time.monotonic() + 30

    while remaining_dsns and time.monotonic() < deadline:
        for dsn in tuple(remaining_dsns):
            try:
                get_stmtcachesize(dsn)
            except oracledb.Error as exc:
                error = exc.args[0]
                if error.full_code == "DPY-2056":
                    remaining_dsns.remove(dsn)
                else:
                    raise

        if remaining_dsns:
            time.sleep(2)

    if remaining_dsns:
        pytest.fail(
            "Timed out waiting for removed GCP configs: "
            + ", ".join(sorted(remaining_dsns))
        )


def wait_for_updated_config(dsn, expected_value):
    deadline = time.monotonic() + 30

    while time.monotonic() < deadline:
        if get_stmtcachesize(dsn) == expected_value:
            return

        time.sleep(2)

    pytest.fail(
        "Timed out waiting for refreshed GCP config "
        f"with stmtcachesize={expected_value}: {dsn}"
    )


@pytest.fixture(scope="module")
def gcs_notifications(skip_unless_run_long_tests, extended_config):
    gcs_subscription_name = extended_config.get_str_value(
        "gcp_gcs_pubsub_subscription_name"
    )
    if gcs_subscription_name:
        drain_subscription(gcs_subscription_name)


@pytest.fixture(scope="module")
def secretmanager_notifications(skip_unless_run_long_tests, extended_config):
    secretmanager_subscription_name = extended_config.get_str_value(
        "gcp_secretmanager_pubsub_subscription_name"
    )
    if secretmanager_subscription_name:
        drain_subscription(secretmanager_subscription_name)


@pytest.fixture
def gcp_listener_configs(test_env, extended_config, gcs_notifications):
    from google.cloud import pubsub_v1, storage

    config = GcpNotifierConfig(test_env, extended_config)
    other_config = GcpNotifierConfig(test_env, extended_config)
    with (
        storage.Client(project=config.project_id) as client,
        pubsub_v1.SubscriberClient() as subscriber,
    ):
        subscription_name = None
        try:
            topic = subscriber.get_subscription(
                request={"subscription": config.subscription_name}
            ).topic
            subscription_name = subscriber.create_subscription(
                request={
                    "name": subscriber.subscription_path(
                        config.project_id,
                        f"oracledb-notifier-{uuid.uuid4().hex}",
                    ),
                    "topic": topic,
                }
            ).name
            for item in (config, other_config):
                item.subscription_name = subscription_name
                item.dsn = (
                    item.dsn.partition("?")[0]
                    + f"?subscriptionname={subscription_name}"
                )
                item.setup(client)
            yield config, other_config
        finally:
            # Delete both objects and wait before removing the subscription.
            try:
                try:
                    other_config.cleanup()
                finally:
                    config.cleanup()
            finally:
                if subscription_name is not None:
                    subscriber.delete_subscription(
                        request={"subscription": subscription_name}
                    )


@pytest.fixture
def gcp_notifier_config(test_env, extended_config, gcs_notifications):
    from google.cloud import storage

    config = GcpNotifierConfig(test_env, extended_config)
    with storage.Client(project=config.project_id) as client:
        config.setup(client)
        yield config
        config.cleanup()


@pytest.fixture
def gcp_secretmanager_notifier_config(
    test_env, extended_config, secretmanager_notifications
):
    from google.cloud import secretmanager

    config = GcpSecretManagerNotifierConfig(test_env, extended_config)
    with secretmanager.SecretManagerServiceClient() as client:
        config.setup(client)
        yield config
        config.delete_secret()


@pytest.fixture
def other_gcp_notifier_config(test_env, extended_config, gcs_notifications):
    from google.cloud import storage

    config = GcpNotifierConfig(test_env, extended_config)
    with storage.Client(project=config.project_id) as client:
        config.setup(client)
        yield config
        config.cleanup()


@pytest.fixture
def other_gcp_secretmanager_notifier_config(
    test_env, extended_config, secretmanager_notifications
):
    from google.cloud import secretmanager

    config = GcpSecretManagerNotifierConfig(test_env, extended_config)
    with secretmanager.SecretManagerServiceClient() as client:
        config.setup(client)
        yield config
        config.delete_secret()


def test_ext_3400(gcp_notifier_config, test_env):
    "E3400 - test real Cloud Storage config cache update notification"
    config = gcp_notifier_config
    initial_stmtcachesize = 23
    updated_stmtcachesize = 37

    config.upload_config(initial_stmtcachesize)
    assert get_stmtcachesize(config.dsn) == initial_stmtcachesize

    config.upload_config(updated_stmtcachesize)
    wait_for_updated_config(config.dsn, updated_stmtcachesize)

    with oracledb.connect(
        user=test_env.main_user,
        password=test_env.main_password,
        dsn=config.dsn,
    ) as conn:
        assert conn.stmtcachesize == updated_stmtcachesize


def test_ext_3401(gcp_notifier_config):
    "E3401 - test real Cloud Storage config cache delete notification"
    config = gcp_notifier_config
    initial_stmtcachesize = 23

    config.upload_config(initial_stmtcachesize)
    assert get_stmtcachesize(config.dsn) == initial_stmtcachesize

    config.delete_config()
    wait_for_removed_configs(config.dsn)


def test_ext_3402(gcp_secretmanager_notifier_config):
    "E3402 - test real Secret Manager version add notification"
    config = gcp_secretmanager_notifier_config
    initial_stmtcachesize = 23
    updated_stmtcachesize = 37
    dsn = config.get_dsn()

    version_name = config.add_config_version(initial_stmtcachesize)
    pinned_dsn = config.get_dsn(version_name)
    assert get_stmtcachesize(dsn) == initial_stmtcachesize
    assert get_stmtcachesize(pinned_dsn) == initial_stmtcachesize

    config.enable_notifications()
    config.add_config_version(updated_stmtcachesize)
    wait_for_updated_config(dsn, updated_stmtcachesize)


def test_ext_3403(gcp_secretmanager_notifier_config):
    "E3403 - test real Secret Manager version disable notification"
    config = gcp_secretmanager_notifier_config
    initial_stmtcachesize = 23

    version_name = config.add_config_version(initial_stmtcachesize)
    latest_dsn = config.get_dsn()
    pinned_dsn = config.get_dsn(version_name)

    assert get_stmtcachesize(latest_dsn) == initial_stmtcachesize
    assert get_stmtcachesize(pinned_dsn) == initial_stmtcachesize

    config.enable_notifications()
    config.client.disable_secret_version(request={"name": version_name})

    wait_for_removed_configs(latest_dsn, pinned_dsn)


def test_ext_3404(gcp_secretmanager_notifier_config):
    "E3404 - test real Secret Manager version destroy notification"
    config = gcp_secretmanager_notifier_config
    initial_stmtcachesize = 23

    version_name = config.add_config_version(initial_stmtcachesize)
    latest_dsn = config.get_dsn()
    pinned_dsn = config.get_dsn(version_name)

    assert get_stmtcachesize(latest_dsn) == initial_stmtcachesize
    assert get_stmtcachesize(pinned_dsn) == initial_stmtcachesize

    config.enable_notifications()
    config.client.destroy_secret_version(request={"name": version_name})

    wait_for_removed_configs(latest_dsn, pinned_dsn)


def test_ext_3405(
    gcp_secretmanager_notifier_config, other_gcp_secretmanager_notifier_config
):
    "E3405 - test secret deletion removes all cached versions of that secret"
    config = gcp_secretmanager_notifier_config
    other_config = other_gcp_secretmanager_notifier_config

    first_stmtcachesize = 23
    second_stmtcachesize = 37
    other_stmtcachesize = 41

    first_version = config.add_config_version(first_stmtcachesize)
    second_version = config.add_config_version(second_stmtcachesize)
    other_version = other_config.add_config_version(other_stmtcachesize)
    first_dsn = config.get_dsn(first_version)
    second_dsn = config.get_dsn(second_version)
    latest_dsn = config.get_dsn()
    other_dsn = other_config.get_dsn(other_version)
    other_latest_dsn = other_config.get_dsn()

    assert get_stmtcachesize(first_dsn) == first_stmtcachesize
    assert get_stmtcachesize(second_dsn) == second_stmtcachesize
    assert get_stmtcachesize(latest_dsn) == second_stmtcachesize
    assert get_stmtcachesize(other_dsn) == other_stmtcachesize
    assert get_stmtcachesize(other_latest_dsn) == other_stmtcachesize

    # Change the other secret without notifications to detect invalidation.
    other_config.add_config_version(other_stmtcachesize + 1)
    config.enable_notifications()
    config.delete_secret()
    wait_for_removed_configs(first_dsn, second_dsn, latest_dsn)

    assert get_stmtcachesize(other_latest_dsn) == other_stmtcachesize


def test_ext_3406(gcp_notifier_config, other_gcp_notifier_config):
    "E3406 - test GCS configurations sharing a Pub/Sub subscription"
    config = gcp_notifier_config
    other_config = other_gcp_notifier_config

    initial_stmtcachesize = 23
    other_stmtcachesize = 24
    updated_stmtcachesize = 37
    other_updated_stmtcachesize = 38

    config.upload_config(initial_stmtcachesize)
    other_config.upload_config(other_stmtcachesize)

    assert get_stmtcachesize(config.dsn) == initial_stmtcachesize
    assert get_stmtcachesize(other_config.dsn) == other_stmtcachesize

    config.upload_config(updated_stmtcachesize)
    wait_for_updated_config(config.dsn, updated_stmtcachesize)

    other_config.upload_config(other_updated_stmtcachesize)
    wait_for_updated_config(other_config.dsn, other_updated_stmtcachesize)


@pytest.mark.parametrize("operation", ["disable", "destroy"])
def test_ext_3407(
    gcp_secretmanager_notifier_config,
    other_gcp_secretmanager_notifier_config,
    operation,
):
    "E3407 - test older-version removal preserves unrelated secret config"
    config = gcp_secretmanager_notifier_config
    other_config = other_gcp_secretmanager_notifier_config

    first_stmtcachesize = 23
    second_stmtcachesize = 37
    other_stmtcachesize = 41

    first_version = config.add_config_version(first_stmtcachesize)
    second_version = config.add_config_version(second_stmtcachesize)
    other_version = other_config.add_config_version(other_stmtcachesize)
    first_dsn = config.get_dsn(first_version)
    second_dsn = config.get_dsn(second_version)
    latest_dsn = config.get_dsn()
    other_dsn = other_config.get_dsn(other_version)
    other_latest_dsn = other_config.get_dsn()

    assert get_stmtcachesize(first_dsn) == first_stmtcachesize
    assert get_stmtcachesize(second_dsn) == second_stmtcachesize
    assert get_stmtcachesize(latest_dsn) == second_stmtcachesize
    assert get_stmtcachesize(other_dsn) == other_stmtcachesize
    assert get_stmtcachesize(other_latest_dsn) == other_stmtcachesize

    # Change the other secret without notifications to detect invalidation.
    other_config.add_config_version(other_stmtcachesize + 1)
    config.enable_notifications()
    if operation == "disable":
        config.client.disable_secret_version(request={"name": first_version})
    else:
        config.client.destroy_secret_version(request={"name": first_version})
    wait_for_removed_configs(first_dsn)

    assert get_stmtcachesize(other_latest_dsn) == other_stmtcachesize


def test_ext_3408(gcp_listener_configs):
    "E3408 - test real Pub/Sub listener stops after its last DSN is removed"

    config, other_config = gcp_listener_configs
    config.upload_config(23)
    other_config.upload_config(24)
    threads = set(threading.enumerate())
    assert get_stmtcachesize(config.dsn) == 23
    (listener_thread,) = (
        thread
        for thread in threading.enumerate()
        if thread not in threads
        and thread.name == "oracledb-gcp-config-listener"
    )
    config.listener_thread = listener_thread
    assert get_stmtcachesize(other_config.dsn) == 24

    config.upload_config(37)
    wait_for_updated_config(config.dsn, 37)
    assert listener_thread.is_alive()

    other_config.delete_config()
    wait_for_removed_configs(other_config.dsn)
    assert listener_thread.is_alive()

    config.delete_config()
    wait_for_removed_configs(config.dsn)
    listener_thread.join(timeout=10)
    assert not listener_thread.is_alive()
