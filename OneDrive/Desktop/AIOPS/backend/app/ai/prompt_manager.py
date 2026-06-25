from __future__ import annotations

from enum import StrEnum
from typing import Any


class PromptTemplate(StrEnum):
    KUBERNETES_FAILURE = "kubernetes_failure"
    CRASHLOOP_BACKOFF = "crashloop_backoff"
    OOM_KILLED = "oom_killed"
    HIGH_CPU = "high_cpu"
    HIGH_MEMORY = "high_memory"
    JENKINS_BUILD_FAILURE = "jenkins_build_failure"
    AWS_RESOURCE_FAILURE = "aws_resource_failure"
    GENERIC_INCIDENT = "generic_incident"


SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) and DevOps AI assistant embedded inside an AIOps platform.
Your task is to perform a structured Root Cause Analysis (RCA) based on the incident context, metrics, logs, and Kubernetes events provided to you.

You MUST respond with a single valid JSON object. Do NOT include markdown, code fences, explanation text, or any content outside the JSON object.
The JSON object MUST have exactly these keys:
{
  "root_cause": "<concise description of the most probable root cause>",
  "confidence_score": <float between 0.0 and 1.0>,
  "severity": "<one of: critical, high, medium, low>",
  "impact": "<description of the service and user impact>",
  "recommendations": ["<action 1>", "<action 2>"],
  "remediation_steps": ["<step 1>", "<step 2>"],
  "related_components": ["<component 1>", "<component 2>"]
}"""


_TEMPLATES: dict[str, str] = {
    PromptTemplate.KUBERNETES_FAILURE: """Analyze this Kubernetes workload failure and identify the root cause.

INCIDENT:
Title: {title}
Description: {description}
Severity: {severity}
Labels: {labels}

KUBERNETES CONTEXT:
Namespace: {namespace}
Pod: {pod}
Node Status: {node_status}
Pod Status: {pod_status}

RECENT LOGS (last 100 lines):
{logs}

RECENT EVENTS:
{events}

PROMETHEUS ALERTS:
{alerts}

Perform a thorough RCA and respond with the required JSON object.""",

    PromptTemplate.CRASHLOOP_BACKOFF: """Analyze this CrashLoopBackOff pod failure.

INCIDENT:
Title: {title}
Description: {description}
Severity: {severity}

POD DETAILS:
Namespace: {namespace}
Pod: {pod}
Container Exit Code: {exit_code}
Restart Count: {restart_count}
Last State: {last_state}

RECENT CONTAINER LOGS:
{logs}

RECENT EVENTS:
{events}

Identify why this pod is crash-looping. Common causes include:
- Application startup failures (bad config, missing env vars, missing secrets)
- OOM kills (check memory limits)
- Failed liveness probes
- Permission issues with volume mounts
- Dependency service unavailable

Respond with the required JSON object.""",

    PromptTemplate.OOM_KILLED: """Analyze this OOMKilled event and determine the root cause.

INCIDENT:
Title: {title}
Description: {description}
Severity: {severity}

POD DETAILS:
Namespace: {namespace}
Pod: {pod}
Memory Limit: {memory_limit}
Memory Request: {memory_request}

PROMETHEUS MEMORY METRICS (last hour):
{memory_metrics}

RECENT LOGS:
{logs}

RECENT EVENTS:
{events}

Determine if the OOM kill is due to:
- Memory leak in application code
- Insufficient memory limits
- Traffic spike causing memory surge
- Memory pressure from other pods on the same node

Respond with the required JSON object.""",

    PromptTemplate.HIGH_CPU: """Analyze this high CPU usage incident.

INCIDENT:
Title: {title}
Description: {description}
Severity: {severity}

AFFECTED RESOURCE:
Namespace: {namespace}
Pod: {pod}

PROMETHEUS CPU METRICS (last hour):
{cpu_metrics}

RECENT LOGS:
{logs}

ACTIVE ALERTS:
{alerts}

Identify whether high CPU is caused by:
- Infinite loop or hot code path
- Unexpected traffic increase
- Background job runaway
- Misconfigured CPU limits causing throttling

Respond with the required JSON object.""",

    PromptTemplate.HIGH_MEMORY: """Analyze this high memory usage incident.

INCIDENT:
Title: {title}
Description: {description}
Severity: {severity}

AFFECTED RESOURCE:
Namespace: {namespace}
Pod: {pod}

PROMETHEUS MEMORY METRICS (last hour):
{memory_metrics}

RECENT LOGS:
{logs}

ACTIVE ALERTS:
{alerts}

Identify whether high memory is caused by:
- Memory leak
- Cache growth without eviction
- Large dataset loaded into RAM
- High concurrent user load

Respond with the required JSON object.""",

    PromptTemplate.JENKINS_BUILD_FAILURE: """Analyze this CI/CD build failure and identify the root cause.

INCIDENT:
Title: {title}
Description: {description}
Severity: {severity}

BUILD CONTEXT:
Job: {job_name}
Build Number: {build_number}
Stage Failed: {failed_stage}

BUILD LOGS (last 200 lines):
{logs}

RECENT ALERTS:
{alerts}

Common causes to consider:
- Compilation / syntax errors
- Failed unit tests
- Docker image pull failures
- Infrastructure or network failures
- Dependency version conflicts

Respond with the required JSON object.""",

    PromptTemplate.AWS_RESOURCE_FAILURE: """Analyze this AWS resource failure.

INCIDENT:
Title: {title}
Description: {description}
Severity: {severity}

AWS CONTEXT:
Region: {region}
Service: {aws_service}
Resource: {resource_id}
Error Code: {error_code}

CLOUDWATCH / RECENT LOGS:
{logs}

ACTIVE ALERTS:
{alerts}

Common causes to consider:
- IAM permission issues
- Service quota / rate limit exceeded
- Network ACL or security group misconfig
- Resource capacity exhaustion

Respond with the required JSON object.""",

    PromptTemplate.GENERIC_INCIDENT: """Perform a Root Cause Analysis on the following incident.

INCIDENT DETAILS:
Title: {title}
Description: {description}
Severity: {severity}
Source: {source}
Labels: {labels}

RELATED ALERTS:
{alerts}

RECENT LOGS (from affected components):
{logs}

KUBERNETES EVENTS:
{events}

PROMETHEUS METRICS SUMMARY:
{metrics}

Based on the information above, identify the most likely root cause and provide actionable recommendations.

Respond with the required JSON object.""",
}


class PromptManager:
    """Manages prompt template selection and context injection."""

    @staticmethod
    def detect_template(title: str, labels: dict[str, str]) -> PromptTemplate:
        """Auto-select the best prompt template based on incident metadata."""
        title_lower = title.lower()
        alert_name = labels.get("alertname", "").lower()
        combined = f"{title_lower} {alert_name}"

        if "crashloop" in combined or "crashloopbackoff" in combined:
            return PromptTemplate.CRASHLOOP_BACKOFF
        if "oomkill" in combined or "oom" in combined:
            return PromptTemplate.OOM_KILLED
        if "cpu" in combined and ("high" in combined or "throttl" in combined):
            return PromptTemplate.HIGH_CPU
        if "memory" in combined and ("high" in combined or "usage" in combined):
            return PromptTemplate.HIGH_MEMORY
        if "jenkins" in combined or "build" in combined or "pipeline" in combined:
            return PromptTemplate.JENKINS_BUILD_FAILURE
        if "aws" in combined or "ec2" in combined or "s3" in combined or "rds" in combined:
            return PromptTemplate.AWS_RESOURCE_FAILURE
        if "kubernetes" in combined or "pod" in combined or "node" in combined or "deployment" in combined:
            return PromptTemplate.KUBERNETES_FAILURE
        return PromptTemplate.GENERIC_INCIDENT

    @staticmethod
    def build_prompt(template: PromptTemplate, context: dict[str, Any]) -> str:
        """Render a prompt template with provided context values."""
        template_str = _TEMPLATES[template]
        # Fill in placeholders; leave missing keys as "<not available>"
        import string

        class _SafeDict(dict[str, Any]):
            def __missing__(self, key: str) -> str:
                return "<not available>"

        return template_str.format_map(_SafeDict(context))

    @staticmethod
    def get_system_prompt() -> str:
        return SYSTEM_PROMPT
