export { providerRouter } from './provider-router'
export { providerMetadataService } from './provider-metadata'
export { capabilityResolver } from './capability-resolver'
export { healthAwareRouter } from './health-aware-routing'
export { rankProviders } from './priority-engine'
export { executePlan } from './parallel-coordinator'
export { executeFallback } from './fallback-engine'
export { aggregateResults } from './result-aggregator'
export { searchAnalyticsService } from './search-analytics'
export type {
  ProviderMetadata, RoutingContext, ProviderRoutingDecision,
  ProviderExecutionPlan, RoutingPolicy, RoutingConfiguration,
  SearchAnalytics, SearchAnalyticsStore, RoutingResult,
} from './routing-types'
export { DEFAULT_ROUTING_POLICY, DEFAULT_ROUTING_CONFIGURATION } from './routing-types'
