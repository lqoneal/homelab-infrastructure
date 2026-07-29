#!/usr/bin/env bash
set -Eeuo pipefail
root="$(git rev-parse --show-toplevel)"
package="$root/engineering/work-orders/GH-ZEUS-OA-CERTIFICATION-001"
test "$root" = "/data/engineering/repositories/homelab"
test "$(git branch --show-current)" = "main"
git diff --check
"$root/scripts/wopctl" validate "$package/immutable-wop.yaml"
"$root/scripts/wop-admissionctl" verify-record \
  --record "$package/admission/ADMISSION-44b52633-b7f5-5160-b402-739dfc518089.json" \
  --repository "$root" \
  --wop "WOP-7d43e7c6-d415-5d3d-939f-f6a064f125d5"
(cd "$package" && sha256sum -c MANIFEST.sha256)
"$root/scripts/engctl" registry validate
echo "GH-ZEUS-OA-CERTIFICATION-001_PACKAGE_VALID=PASS"
