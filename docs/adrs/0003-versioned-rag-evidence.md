# ADR 0003: Structured, versioned evidence snapshots

Status: accepted; real-model generation behavior pending GPU verification.

Replace free-form numbered citations at the gateway boundary with JSON steps
referencing stable retrieved chunk IDs. Server-side mapping determines source
pages; the model cannot choose arbitrary page numbers or outside evidence IDs.
Save the full manual identity, excerpt checksums, steps and generation provenance
in the answer transaction. Preserve old unversioned records without invented data.

The new boundary deliberately rejects v1/new uncited outputs. Deploy matching
gateway modules before creating new real answers. Explicit clarification and
insufficient-evidence outcomes complete jobs without pretending to answer.
Reference integrity does not establish semantic support; labelled quality evaluation
is still required. Manual PDF hash checks prevent silently opening a newer document
for an answer based on an older version.
