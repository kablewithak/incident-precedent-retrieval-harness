import type { FactValue } from "@/lib/contracts"

export type ScenarioKey = "pool" | "conflict" | "insufficient" | "degraded"

export type Scenario = {
  key: ScenarioKey
  label: string
  summary: string
  facts: Record<string, FactValue>
  providerAvailable: boolean
  selectionEnabled: boolean
  service: string
  component: string
  changeContext: string
  signals: string[]
}

export const factDefinitions = [
  ["database_connection_pool_utilization", "Database connection-pool utilization"],
  ["database_connection_acquire_latency", "Database connection-acquire latency"],
  ["active_database_connections", "Active database connections"],
  ["migration_lock_waits", "Migration lock waits"],
  ["error_rate_by_component", "Component error rate"],
  ["worker_deployment_version", "Worker deployment version"],
  ["queue_depth", "Queue depth"],
  ["consumer_error_rate", "Consumer error rate"],
] as const

export const services = ["payments-api", "auth-service", "webhook-delivery-service", "feature-flag-service", "notification-service", "workflow-service"]
export const components = ["postgres-client-pool", "auth-db-client", "delivery-store-client", "delivery-consumer", "delivery-store-writer", "flag-evaluator", "event-consumer", "notification-worker", "cache-update-worker", "postgres-primary"]
export const changeContexts = ["none", "configuration", "deployment", "migration", "feature_flag", "dependency", "unknown"]
export const signalDefinitions = [
  ["connection_pool_pressure", "Connection-pool pressure"],
  ["active_connection_pressure", "Active connection pressure"],
  ["authentication_failure", "Authentication failure"],
  ["readiness_failure", "Readiness failure"],
  ["component_error_pressure", "Component error pressure"],
  ["queue_backlog", "Queue backlog"],
  ["retry_amplification", "Retry amplification"],
] as const

export const scenarios: Record<ScenarioKey, Scenario> = {
  pool: {
    key: "pool",
    label: "Pool-pressure evidence",
    summary: "Payments API requests are timing out while database connection-pool utilisation and connection-acquire latency are elevated. Active database connections are high. Migration lock waits are absent.",
    facts: { database_connection_pool_utilization: "confirmed", database_connection_acquire_latency: "confirmed", active_database_connections: "confirmed", migration_lock_waits: "contradicted", error_rate_by_component: "confirmed" },
    providerAvailable: true,
    selectionEnabled: true,
    service: "payments-api",
    component: "postgres-client-pool",
    changeContext: "none",
    signals: ["connection_pool_pressure", "active_connection_pressure"],
  },
  conflict: {
    key: "conflict",
    label: "Conflicting evidence",
    summary: "After a worker release, webhook processing slowed and backlog increased. Worker deployment version, queue depth, consumer error rate, database pool utilisation, connection-acquire latency, active database connections, and component error rate are all elevated. Migration lock waits are absent.",
    facts: { worker_deployment_version: "confirmed", queue_depth: "confirmed", consumer_error_rate: "confirmed", database_connection_pool_utilization: "confirmed", database_connection_acquire_latency: "confirmed", active_database_connections: "confirmed", error_rate_by_component: "confirmed", migration_lock_waits: "contradicted" },
    providerAvailable: true,
    selectionEnabled: false,
    service: "payments-api",
    component: "postgres-client-pool",
    changeContext: "none",
    signals: [],
  },
  insufficient: {
    key: "insufficient",
    label: "No safe match",
    summary: "A user reports a vague service slowdown, but there are no confirmed queue, migration, or database-pool verification facts.",
    facts: {},
    providerAvailable: true,
    selectionEnabled: false,
    service: "payments-api",
    component: "postgres-client-pool",
    changeContext: "none",
    signals: [],
  },
  degraded: {
    key: "degraded",
    label: "Evidence service unavailable",
    summary: "Payments API requests are timing out while database connection-pool utilisation and connection-acquire latency are elevated. Active database connections are high.",
    facts: { database_connection_pool_utilization: "confirmed", database_connection_acquire_latency: "confirmed", active_database_connections: "confirmed", migration_lock_waits: "contradicted", error_rate_by_component: "confirmed" },
    providerAvailable: false,
    selectionEnabled: false,
    service: "payments-api",
    component: "postgres-client-pool",
    changeContext: "none",
    signals: [],
  },
}
