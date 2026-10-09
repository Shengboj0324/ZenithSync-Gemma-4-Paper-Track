"""Local evaluation settings matching the acquired competition README section 7.2.

These settings delegate to ADK; they do not implement a custom compactor or
guarantee that its summaries preserve tool observations. Hidden-grader parity
and long-context behavior require separate evidence.
"""

from importlib.metadata import version


def competition_context_configs():
    if version('google-adk') != '1.36.1':
        raise ValueError('Context behavior must be requalified for this ADK version')
    from google.adk.agents.context_cache_config import ContextCacheConfig
    from google.adk.apps._configs import EventsCompactionConfig
    return {
        'events_compaction_config': EventsCompactionConfig(
            compaction_interval=5, overlap_size=2,
            token_threshold=14336, event_retention_size=5),
        'context_cache_config': ContextCacheConfig(
            min_tokens=2048, ttl_seconds=1800, cache_intervals=10),
    }
