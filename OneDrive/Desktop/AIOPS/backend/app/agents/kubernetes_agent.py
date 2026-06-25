from __future__ import annotations

import datetime
import logging
from typing import Any
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException

logger = logging.getLogger(__name__)


class KubernetesAgent:
    def __init__(self, kubeconfig_path: str | None = None) -> None:
        self.kubeconfig_path = kubeconfig_path
        self._initialized = False

    def _ensure_client(self) -> None:
        if self._initialized:
            return
        try:
            if self.kubeconfig_path:
                config.load_kube_config(config_file=self.kubeconfig_path)
            else:
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()
            self._initialized = True
            logger.info("Kubernetes API client initialized successfully.")
        except Exception as e:
            logger.error("Failed to load Kubernetes configuration: %s", e)
            raise

    @property
    def core_api(self) -> client.CoreV1Api:
        self._ensure_client()
        return client.CoreV1Api()

    @property
    def apps_api(self) -> client.AppsV1Api:
        self._ensure_client()
        return client.AppsV1Api()

    def list_namespaces(self) -> list[client.V1Namespace]:
        return list(self.core_api.list_namespace().items)

    def list_pods(self, namespace: str | None = None) -> list[client.V1Pod]:
        if namespace:
            return list(self.core_api.list_namespaced_pod(namespace).items)
        return list(self.core_api.list_pod_for_all_namespaces().items)

    def get_pod(self, name: str, namespace: str) -> client.V1Pod:
        return self.core_api.read_namespaced_pod(name, namespace)

    def get_pod_logs(
        self,
        name: str,
        namespace: str,
        container: str | None = None,
        tail_lines: int | None = None,
    ) -> str:
        kwargs: dict[str, Any] = {}
        if container:
            kwargs["container"] = container
        if tail_lines:
            kwargs["tail_lines"] = tail_lines
        return str(self.core_api.read_namespaced_pod_log(name, namespace, **kwargs))

    def get_pod_events(self, name: str, namespace: str) -> list[client.CoreV1Event]:
        field_selector = f"involvedObject.name={name}"
        return list(
            self.core_api.list_namespaced_event(namespace, field_selector=field_selector).items
        )

    def list_deployments(self, namespace: str | None = None) -> list[client.V1Deployment]:
        if namespace:
            return list(self.apps_api.list_namespaced_deployment(namespace).items)
        return list(self.apps_api.list_deployment_for_all_namespaces().items)

    def get_deployment(self, name: str, namespace: str) -> client.V1Deployment:
        return self.apps_api.read_namespaced_deployment(name, namespace)

    def restart_deployment(self, name: str, namespace: str) -> client.V1Deployment:
        now = datetime.datetime.now(datetime.UTC).isoformat()
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": now
                        }
                    }
                }
            }
        }
        return self.apps_api.patch_namespaced_deployment(name, namespace, body)

    def scale_deployment(self, name: str, namespace: str, replicas: int) -> client.V1Deployment:
        body = {"spec": {"replicas": replicas}}
        return self.apps_api.patch_namespaced_deployment(name, namespace, body)

    def rollback_deployment(
        self,
        name: str,
        namespace: str,
        revision: int = 0,
    ) -> tuple[client.V1Deployment, int]:
        rs_list = self.apps_api.list_namespaced_replica_set(namespace)
        
        matching_rss = []
        for rs in rs_list.items:
            owned = False
            if rs.metadata.owner_references:
                for owner in rs.metadata.owner_references:
                    if owner.kind == "Deployment" and owner.name == name:
                        owned = True
                        break
            if owned:
                matching_rss.append(rs)

        if not matching_rss:
            raise ApiException(status=404, reason=f"No ReplicaSets found for deployment {name}")

        rss_with_revision = []
        for rs in matching_rss:
            rev_str = rs.metadata.annotations.get("deployment.kubernetes.io/revision")
            if rev_str:
                try:
                    rss_with_revision.append((int(rev_str), rs))
                except ValueError:
                    pass

        if not rss_with_revision:
            raise ApiException(status=404, reason=f"No revision history found for deployment {name}")

        rss_with_revision.sort(key=lambda x: x[0], reverse=True)

        target_rs = None
        target_revision = 0
        if revision == 0:
            if len(rss_with_revision) < 2:
                raise ApiException(status=400, reason=f"No previous revision available to rollback deployment {name}")
            target_revision = rss_with_revision[1][0]
            target_rs = rss_with_revision[1][1]
        else:
            for rev, rs in rss_with_revision:
                if rev == revision:
                    target_rs = rs
                    target_revision = rev
                    break
            if not target_rs:
                raise ApiException(status=404, reason=f"Revision {revision} not found for deployment {name}")

        api_client = client.ApiClient()
        template_dict = api_client.sanitize_for_serialization(target_rs.spec.template)

        body = {
            "spec": {
                "template": template_dict
            }
        }
        patched_deployment = self.apps_api.patch_namespaced_deployment(name, namespace, body)
        return patched_deployment, target_revision

    def list_nodes(self) -> list[client.V1Node]:
        return list(self.core_api.list_node().items)
