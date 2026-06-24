"""Controlled vocabulary for the source-grounded synthetic dataset."""

from enum import Enum


class RecordOrigin(str, Enum):
    """How a record entered the fictional RelayOps archive."""

    SOURCE_GROUNDED = "source_grounded"
    CONTROLLED_VARIANT = "controlled_variant"
    SYNTHETIC_NO_PRECEDENT = "synthetic_no_precedent"


class SourceUsageMode(str, Enum):
    """How public material may inform a fictional record."""

    LICENSED_SOURCE = "licensed_source"
    CITED_REFERENCE = "cited_reference"
    MANUALLY_AUTHORED_VARIANT = "manually_authored_variant"


class IncidentFamily(str, Enum):
    """The eight fixed incident families for the 50-hour scope."""

    DEPLOYMENT_WORKER_CRASH_LOOP = "deployment_worker_crash_loop"
    QUEUE_BACKLOG_CONSUMER_FAILURE = "queue_backlog_consumer_failure"
    DATABASE_MIGRATION_LOCK_CONTENTION = "database_migration_lock_contention"
    CONNECTION_POOL_EXHAUSTION = "connection_pool_exhaustion"
    CACHE_STAMPEDE_INVALIDATION_FAILURE = "cache_stampede_invalidation_failure"
    THIRD_PARTY_WEBHOOK_PROVIDER_DEGRADATION = "third_party_webhook_provider_degradation"
    FEATURE_FLAG_ROLLOUT_REGRESSION = "feature_flag_rollout_regression"
    RATE_LIMIT_OR_AUTH_CONFIGURATION_REGRESSION = (
        "rate_limit_or_auth_configuration_regression"
    )


class ProcedureStatus(str, Enum):
    """Lifecycle state for candidate investigation procedures."""

    CURRENT = "current"
    STALE = "stale"
    RETIRED = "retired"


class EvidenceDecisionState(str, Enum):
    """The only final decision states permitted by the product contract."""

    EVIDENCE_FOUND = "evidence_found"
    EVIDENCE_FOUND_WITH_CONFLICT = "evidence_found_with_conflict"
    MISSING_CRITICAL_FACTS = "missing_critical_facts"
    INSUFFICIENT_PRECEDENT = "insufficient_precedent"
    PROVIDER_DEGRADED = "provider_degraded"


class ChangeContext(str, Enum):
    """Controlled context of a change preceding an incident."""

    DEPLOYMENT = "deployment"
    MIGRATION = "migration"
    FEATURE_FLAG = "feature_flag"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"
    NONE = "none"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Fictional incident severity vocabulary."""

    SEV_1 = "sev_1"
    SEV_2 = "sev_2"
    SEV_3 = "sev_3"
    SEV_4 = "sev_4"


class RecoveryState(str, Enum):
    """Observed recovery state, not a remediation instruction."""

    RECOVERED = "recovered"
    PARTIALLY_RECOVERED = "partially_recovered"
    UNRESOLVED = "unresolved"
    UNKNOWN = "unknown"


class RequiredVerificationFact(str, Enum):
    """Facts a responder may need before treating precedent as applicable."""

    CONSUMER_ERROR_RATE = "consumer_error_rate"
    WORKER_DEPLOYMENT_VERSION = "worker_deployment_version"
    QUEUE_DEPTH = "queue_depth"
    MIGRATION_LOCK_WAITS = "migration_lock_waits"
    ACTIVE_DATABASE_CONNECTIONS = "active_database_connections"
    CACHE_MISS_RATE = "cache_miss_rate"
    PROVIDER_STATUS = "provider_status"
    FEATURE_FLAG_STATE = "feature_flag_state"
    RATE_LIMIT_CONFIGURATION = "rate_limit_configuration"
    AUTHENTICATION_ERROR_RATE = "authentication_error_rate"
    ERROR_RATE_BY_COMPONENT = "error_rate_by_component"
    REGION = "region"
