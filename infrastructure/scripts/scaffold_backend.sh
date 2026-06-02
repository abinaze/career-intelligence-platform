#!/usr/bin/env bash
# Run this from the repo root to scaffold the backend directory structure.
# Usage: bash infrastructure/scripts/scaffold_backend.sh

set -e

BASE="apps/backend"

mkdir -p \
  "$BASE/src/api/v1/endpoints" \
  "$BASE/src/api/v1/dependencies" \
  "$BASE/src/api/middleware" \
  "$BASE/src/core/config" \
  "$BASE/src/core/security" \
  "$BASE/src/core/logging" \
  "$BASE/src/db/models" \
  "$BASE/src/db/repositories" \
  "$BASE/src/db/migrations/versions" \
  "$BASE/src/services/auth" \
  "$BASE/src/services/profile" \
  "$BASE/src/services/psychometric" \
  "$BASE/src/services/recommendation" \
  "$BASE/src/services/career_ontology" \
  "$BASE/src/services/analytics" \
  "$BASE/src/ai/embeddings" \
  "$BASE/src/ai/psychometric_engine" \
  "$BASE/src/ai/recommendation_engine" \
  "$BASE/src/ai/explainability" \
  "$BASE/src/schemas/requests" \
  "$BASE/src/schemas/responses" \
  "$BASE/src/workers" \
  "$BASE/src/scripts" \
  "$BASE/tests/unit/services" \
  "$BASE/tests/unit/api" \
  "$BASE/tests/integration" \
  "$BASE/tests/fixtures" \
  "$BASE/data/onet" \
  "$BASE/data/esco" \
  "$BASE/data/psychometric"

find "$BASE" -type d -empty -exec touch {}/__init__.py \;

echo "Backend scaffold complete."
