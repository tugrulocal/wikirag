# Recommendation

For production deployment of this HW3 assistant, keep the local-first architecture for development and grading, but separate the concerns into managed equivalents when moving beyond a laptop. Preserve the ingestion, chunking, retrieval, and grounding boundaries so the same prompt discipline and metadata filtering rules can survive migration.

If the system needs to scale, move from local Chroma to a managed vector backend and from local SQLite to a managed relational store, but keep the same category metadata contract (`person` and `place`). Add observability for ingestion time, embedding throughput, retrieval latency, and generation latency so model changes can be measured rather than guessed.

For quality, keep the grounding rule strict in production too: if the context does not support the answer, the assistant must say `I don't know`. That discipline is more important than model size for user trust in a fact-oriented assistant.
