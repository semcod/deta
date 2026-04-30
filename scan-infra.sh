#!/bin/bash
# scan-infra.sh — Phase 0: Bash prototype for infrastructure scanning

SCAN_DEPTH=3
OUT="infra-map.json"

echo "{\"services\":{}}" > $OUT

# Find all docker-compose*.yml up to depth 3
echo "[SCAN] Scanning docker-compose files..."
find . -maxdepth $SCAN_DEPTH -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | while read f; do
    echo "[SCAN] $f"
    # Extract service names
    if command -v yq &> /dev/null; then
        yq e '.services | keys | .[]' "$f" 2>/dev/null
    else
        echo "[WARN] yq not installed, skipping YAML parsing"
    fi
done

# Healthchecks
echo "[SCAN] Extracting healthchecks..."
if command -v yq &> /dev/null; then
    find . -maxdepth $SCAN_DEPTH \( -name "docker-compose*.yml" -o -name "docker-compose*.yaml" \) | xargs -I{} \
        yq e '.services.[] | select(.healthcheck) | .healthcheck.test' {} 2>/dev/null
fi

# OpenAPI paths
echo "[SCAN] Scanning OpenAPI files..."
find . -maxdepth $SCAN_DEPTH \( -name "openapi*.yml" -o -name "openapi*.yaml" -o -name "openapi*.json" \) | while read f; do
    echo "[SCAN] $f"
    if command -v yq &> /dev/null; then
        yq e '.paths | keys | .[]' "$f" 2>/dev/null
    fi
done

echo "[DONE] Scan complete. Results would be written to $OUT"
