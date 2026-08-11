"""Mission-scoped publication-candidate authority resolution.

This module resolves publication candidates from the live mission/WOP
projection and qualified publication manifests.  It deliberately does not
stage, commit, push, or synchronize anything.  A dirty path is never
publication authority by itself.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping

import yaml

from scripts.lib.emp.canonical_lifecycle_resolver import resolve as resolve_lifecycle
from scripts.lib.emp.production_execution import digest
from scripts.lib.emp.repository_state_view import project as project_repository


MANIFEST_NAME = "PUBLICATION-CANDIDATE-MANIFEST.md"
MANIFEST_SUFFIXES = {".json", ".yaml", ".yml", ".md"}
PATH_RE = re.compile(r"(?<![A-Za-z0-9_./-])((?:engineering|scripts|docs|services|\.zeus)/[^\s`|,)]+)")
MISSION_RE = re.compile(r"(?:mission[_ ]id|primary[_ ]mission|mission)\s*[:=]\s*([A-Za-z0-9._-]+)", re.I)
WOP_RE = re.compile(r"(?:wop[_ ]id|authoritative[_ ]wop|wop)\s*[:=]\s*(WOP-[A-Za-z0-9._-]+)", re.I)


class CandidateAuthorityError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def _text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    try:
        value = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return {}
    return value if isinstance(value, dict) else {}


def _normalise_path(value: str, root: Path) -> str:
    value = value.strip().strip("`'\".,:;()[]")
    if not value or value in {".", "this", "directory", "evidence directory"}:
        return ""
    candidate = Path(value)
    if candidate.is_absolute():
        try:
            candidate = candidate.resolve().relative_to(root.resolve())
        except ValueError:
            return ""
    return candidate.as_posix().lstrip("./")


def _expand_path(root: Path, value: str) -> list[str]:
    relative = _normalise_path(value, root)
    if not relative:
        return []
    path = root / relative
    if path.is_dir():
        return sorted(item.relative_to(root).as_posix() for item in path.rglob("*") if item.is_file())
    return [relative]


def _manifest_paths(root: Path, manifest: Path, structured: Mapping[str, Any], text: str) -> list[str]:
    values: list[str] = []
    for key in ("candidate_paths", "paths", "files", "candidate_files"):
        value = structured.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value if isinstance(item, (str, Path)))
    # Markdown manifests use bullets/code blocks for the authoritative list.
    # Restrict extraction to candidate-oriented sections so command examples
    # and prose cannot become publication authority.
    in_candidate_section = False
    in_code = False
    lines = text.splitlines()
    frontmatter_end = 0
    if lines and lines[0].strip() == "---":
        frontmatter_end = next((index for index, value in enumerate(lines[1:], start=1) if value.strip() == "---"), 0)
    for index, line in enumerate(lines):
        stripped = line.strip()
        if frontmatter_end and index <= frontmatter_end:
            continue
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if stripped.startswith("#"):
            lower = stripped.lower()
            in_candidate_section = any(token in lower for token in ("candidate", "corrective path", "bounded file", "wave-specific"))
            continue
        is_bullet = bool(re.match(r"^(?:[-*+]\s+|\d+[.)]\s+)", stripped))
        if not in_candidate_section and not in_code and not is_bullet and not re.fullmatch(r"(?:engineering|scripts|docs|services|\.zeus)/\S+", stripped.strip("`")):
            continue
        if not in_code and not is_bullet and not re.fullmatch(r"(?:engineering|scripts|docs|services|\.zeus)/\S+", stripped.strip("`")):
            continue
        values.extend(match.rstrip(".,:;)") for match in PATH_RE.findall(line))
        if is_bullet and not PATH_RE.findall(line):
            token = re.sub(r"^(?:[-*+]\s+|\d+[.)]\s+)", "", stripped).strip("`'\".,:;()[]")
            if re.fullmatch(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*", token):
                values.append(token)
        # A bullet naming this evidence directory is an authoritative request
        # for the package, not a request to publish historical evidence.
        if "this evidence directory" in stripped.lower():
            values.append(str(manifest.parent))
    expanded: list[str] = []
    for value in values:
        expanded.extend(_expand_path(root, value))
    return sorted(set(expanded))


def _context(root: Path, manifest: Path) -> tuple[str, str, str]:
    package = manifest.parent
    texts = "\n".join(_text(path) for path in sorted(package.glob("*.md")))
    mission = next((match.group(1).upper() for match in MISSION_RE.finditer(texts)), "")
    wop = next((match.group(1).upper() for match in WOP_RE.finditer(texts)), "")
    return mission, wop, texts


def _qualification(text: str) -> tuple[str, str]:
    upper = text.upper()
    if re.search(r"\bQUALIFICATION_STATE\s*=\s*(?:QUALIFIED|PASS|IMPLEMENTED)\b", upper):
        return "QUALIFIED", "source declares qualified state"
    if re.search(r"\bQUALIFICATION_STATE\s*=\s*(?:BLOCKED|FAIL|UNQUALIFIED)\b", upper):
        return "BLOCKED", "source declares unqualified state"
    if re.search(r"\b(?:STATUS|RESULT)\s*=\s*(?:BLOCKED|FAIL|FAILED|UNRESOLVED)", upper):
        return "BLOCKED", "qualification record is blocked or failed"
    if re.search(r"\b(?:SOURCE_CLASSIFICATION|PUBLICATION_STATE)\s*=\s*HISTORICAL_ONLY\b", upper) or re.search(r"\bHISTORICAL_MANIFEST\s*=\s*YES\b", upper):
        return "HISTORICAL_ONLY", "manifest is explicitly historical"
    if any(token in upper for token in ("QUALIFIED", "IMPLEMENTED", "VALIDATION=PASS", "STATUS=AWAITING_OPERATOR_REVIEW", "RESULT=PASS")):
        return "QUALIFIED", "qualified completion/evidence record is present"
    return "UNQUALIFIED", "no current qualification result was found"


def _publication_state(text: str) -> tuple[str, str]:
    upper = text.upper()
    if re.search(r"\b(?:SOURCE_CLASSIFICATION|PUBLICATION_STATE)\s*=\s*HISTORICAL_ONLY\b", upper):
        return "HISTORICAL_ONLY", "source is explicitly historical"
    if re.search(r"\b(?:PUBLISHED|PUBLICATION(?:_STATE)?)\s*=\s*(?:YES|COMPLETE|QUALIFIED|PUBLISHED|ALREADY_PUBLISHED)\b", upper):
        return "ALREADY_PUBLISHED", "source records state that publication completed"
    if re.search(r"\b(?:PUBLISHED|PUBLICATION(?:_STATE)?)\s*=\s*(?:NO|NOT_PERFORMED|UNPUBLISHED|QUALIFIED_UNPUBLISHED)\b", upper) or "PUBLICATION WAS NOT PERFORMED" in upper or "NO FILES WERE STAGED" in upper:
        return "QUALIFIED_UNPUBLISHED", "source records state that publication has not occurred"
    # A candidate manifest without publication evidence remains unproven, not
    # silently eligible.
    return "UNKNOWN", "publication state is not recorded"


def _source_records(root: Path, mission_id: str, wop_id: str, explicit_manifest: Path | str | None) -> list[dict[str, Any]]:
    manifests: list[Path] = []
    if explicit_manifest:
        manifests.append(Path(explicit_manifest).resolve())
    manifests.extend(sorted(root.glob("engineering/evidence/**/PUBLICATION-CANDIDATE-MANIFEST.*")))
    records: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for manifest in manifests:
        if manifest in seen or manifest.suffix.lower() not in MANIFEST_SUFFIXES or not manifest.is_file():
            continue
        seen.add(manifest)
        text = _text(manifest)
        structured = _frontmatter(text)
        if manifest.suffix.lower() in {".json", ".yaml", ".yml"}:
            try:
                loaded = yaml.safe_load(text) or {}
            except yaml.YAMLError:
                loaded = {}
            if isinstance(loaded, dict):
                structured = loaded
        context_mission, context_wop, context = _context(root, manifest)
        declared_mission = str(structured.get("mission_id") or context_mission).upper()
        declared_wop = str(structured.get("wop_id") or context_wop).upper()
        # Some legacy Markdown evidence records use the canonical identities
        # in prose rather than a `MISSION_ID=` front matter field.  Exact
        # equality against the live identities is still authoritative here;
        # unrelated text is never accepted as a match.
        if not declared_mission and mission_id in context:
            declared_mission = mission_id
        if not declared_wop and wop_id in context:
            declared_wop = wop_id
        if declared_mission and declared_mission != mission_id and declared_wop != wop_id:
            continue
        if not declared_mission and not declared_wop:
            continue
        if declared_wop and declared_wop != wop_id:
            continue
        qualification, qualification_reason = _qualification(context + "\n" + text)
        publication_state, publication_reason = _publication_state(context + "\n" + text)
        declared_qualification = str(structured.get("qualification_state") or "").upper()
        declared_publication = str(structured.get("publication_state") or "").upper()
        if declared_qualification in {"QUALIFIED", "PASS", "IMPLEMENTED"}:
            qualification, qualification_reason = "QUALIFIED", "manifest declares qualified source"
        elif declared_qualification in {"HISTORICAL_ONLY", "HISTORICAL"}:
            qualification, qualification_reason = "HISTORICAL_ONLY", "manifest declares historical source"
        elif declared_qualification in {"BLOCKED", "FAIL", "UNQUALIFIED"}:
            qualification, qualification_reason = "BLOCKED", "manifest declares unqualified source"
        if declared_publication in {"NOT_PERFORMED", "NO", "UNPUBLISHED", "QUALIFIED_UNPUBLISHED"}:
            publication_state, publication_reason = "QUALIFIED_UNPUBLISHED", "manifest declares unpublished source"
        elif declared_publication in {"HISTORICAL_ONLY", "HISTORICAL"}:
            publication_state, publication_reason = "HISTORICAL_ONLY", "manifest declares historical source"
            qualification, qualification_reason = "HISTORICAL_ONLY", "manifest declares historical source"
        elif declared_publication in {"PUBLISHED", "YES", "COMPLETE", "ALREADY_PUBLISHED"}:
            publication_state, publication_reason = "ALREADY_PUBLISHED", "manifest declares published source"
        paths = _manifest_paths(root, manifest, structured, text)
        source_id = hashlib.sha256(f"{manifest}:{hashlib.sha256(text.encode()).hexdigest()}".encode()).hexdigest()
        if qualification == "HISTORICAL_ONLY":
            classification = "HISTORICAL_ONLY"
        elif qualification != "QUALIFIED":
            classification = "BLOCKED"
        elif publication_state == "ALREADY_PUBLISHED":
            classification = "ALREADY_PUBLISHED"
        elif publication_state == "QUALIFIED_UNPUBLISHED":
            classification = "QUALIFIED_UNPUBLISHED"
        else:
            classification = "BLOCKED"
        records.append({
            "source_id": source_id,
            "source_path": _display_path(manifest, root),
            "source_type": "PUBLICATION_CANDIDATE_MANIFEST",
            "mission_id": mission_id,
            "wop_id": wop_id,
            "qualification_state": qualification,
            "qualification_reason": qualification_reason,
            "publication_state": classification,
            "publication_reason": publication_reason,
            "publication_manifest": _display_path(manifest, root),
            "authority": {"type": "QUALIFIED_MISSION_EVIDENCE", "source": _display_path(manifest, root), "source_id": source_id},
            "dependency_relationship": structured.get("dependency_relationship", "DIRECT"),
            "dependencies": [str(item) for item in (structured.get("dependencies") or structured.get("required_dependencies") or []) if isinstance(item, (str, Path))],
            "candidate_intent": str(structured.get("candidate_intent") or structured.get("scope") or "").strip(),
            "publication_cohort": str(
                structured.get("publication_cohort")
                or structured.get("publication_unit")
                or structured.get("publication_unit_id")
                or structured.get("publication_boundary_id")
                or ""
            ).strip(),
            "candidate_paths": paths,
            "context_digest": digest({
                "mission_id": declared_mission,
                "wop_id": declared_wop,
                # Generated completion summaries may record the derived
                # candidate digest. Exclude their mutable prose from the
                # source identity while retaining the immutable manifest and
                # stable package evidence in the context digest.
                "text": text + "\n" + "\n".join(
                    _text(path) for path in sorted(manifest.parent.glob("*.md"))
                    if path.name not in {"COMPLETION-REPORT.md", MANIFEST_NAME}
                ),
            }),
        })
    return records


def _explicit_manifest_identity(manifest: Path | str) -> tuple[str, str]:
    path = Path(manifest).resolve()
    text = _text(path)
    value = _frontmatter(text)
    if path.suffix.lower() in {".json", ".yaml", ".yml"}:
        try:
            loaded = yaml.safe_load(text) or {}
        except yaml.YAMLError as error:
            raise CandidateAuthorityError("MANIFEST_INVALID", str(error)) from error
        if isinstance(loaded, dict):
            value = loaded
    mission = str(value.get("mission_id") or "").strip().upper()
    wop = str(value.get("wop_id") or "").strip().upper()
    if not mission:
        match = re.search(r"(?:MISSION_ID|MISSION)\s*[:=]\s*([A-Za-z0-9._-]+)", text, re.I)
        mission = match.group(1).upper() if match else ""
    if not wop:
        match = re.search(r"(?:WOP_ID|WOP)\s*[:=]\s*(WOP-[A-Za-z0-9._-]+)", text, re.I)
        wop = match.group(1).upper() if match else ""
    if not mission or not wop:
        raise CandidateAuthorityError("MANIFEST_IDENTITY_MISSING", "explicit manifest must bind a mission and WOP")
    return mission, wop


def _path_publication_state(root: Path, path: str, head: str) -> str:
    environment = {**__import__("os").environ, "GIT_TERMINAL_PROMPT": "0"}
    tracked = __import__("subprocess").run(["git", "-C", str(root), "cat-file", "-e", f"{head}:{path}"], capture_output=True, check=False, env=environment)
    if tracked.returncode != 0:
        return "QUALIFIED_UNPUBLISHED"
    result = __import__("subprocess").run(["git", "-C", str(root), "diff", "--quiet", head, "--", path], capture_output=True, check=False, env=environment)
    if result.returncode == 0 and (root / path).is_file():
        return "ALREADY_PUBLISHED"
    if result.returncode not in (0, 1):
        raise CandidateAuthorityError("GIT_CANDIDATE_PROJECTION_FAILED", result.stderr.decode(errors="replace").strip() or "git diff failed")
    return "QUALIFIED_UNPUBLISHED"


def resolve(root: Path | str, mission_id: str, *, runtime_root: Path | str | None = None,
            manifest: Path | str | None = None,
            lifecycle_projection: Mapping[str, Any] | None = None,
            cohort_id: str | None = None) -> dict[str, Any]:
    """Resolve the exact qualified, unpublished candidate set for one mission."""
    repository = Path(root).resolve()
    mission = str(mission_id).strip().upper()
    live = dict(lifecycle_projection or resolve_lifecycle(repository, mission, runtime_root=runtime_root))
    if live.get("result") != "PASS" and manifest:
        # Explicit manifests are a bounded engineering/test fallback only.
        # They may establish identity for isolated controller tests, but never
        # override a contradictory live mission projection.
        explicit_mission, explicit_wop = _explicit_manifest_identity(manifest)
        if explicit_mission != mission:
            return {"result": "FAIL", "mission_id": mission, "candidate_sources": [], "candidate_paths": [], "blocked": [{"code": "MANIFEST_MISSION_MISMATCH", "reason": "explicit manifest does not bind requested mission"}], "next_authorized_action": "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY", "read_only": True}
        live = {"result": "PASS", "mission_id": explicit_mission, "wop_id": explicit_wop, "projection_source": "EXPLICIT_QUALIFIED_MANIFEST_FALLBACK", "read_only": True}
    if live.get("result") != "PASS":
        return {"result": "FAIL", "mission_id": mission, "candidate_sources": [], "candidate_paths": [], "blocked": [{"code": "MISSION_PROJECTION_INVALID", "reason": live.get("blockers")}], "next_authorized_action": "RESOLVE_MISSION_PROJECTION", "read_only": True}
    wop_id = str(live.get("wop_id") or "").upper()
    if not wop_id:
        return {"result": "FAIL", "mission_id": mission, "candidate_sources": [], "candidate_paths": [], "blocked": [{"code": "WOP_PROJECTION_MISSING", "reason": "live mission projection has no WOP identity"}], "next_authorized_action": "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY", "read_only": True}
    projection = project_repository(repository)
    if projection.get("result") != "PASS":
        return {"result": "FAIL", "mission_id": mission, "wop_id": wop_id, "candidate_sources": [], "candidate_paths": [], "blocked": [{"code": "REPOSITORY_PROJECTION_INVALID", "reason": projection.get("errors")}], "next_authorized_action": "RESOLVE_REPOSITORY_PROJECTION", "read_only": True}
    records = _source_records(repository, mission, wop_id, manifest)
    qualified = [record for record in records if record["publication_state"] == "QUALIFIED_UNPUBLISHED"]
    cohort = None
    bound_cohort = cohort_id is not None
    bound_member_ids: set[str] = set()
    if cohort_id:
        from scripts.lib.emp import publication_cohort

        cohort = publication_cohort.load_bound(repository, cohort_id, runtime_root=runtime_root)
        if not cohort:
            return {
                "result": "FAIL", "mission_id": mission, "wop_id": wop_id,
                "candidate_sources": [], "candidate_paths": [], "candidate_traceability": [],
                "candidate_digest": None, "classification_digest": None,
                "already_published": [], "historical_sources": [], "already_published_sources": [],
                "excluded_paths": [], "excluded_sources": [], "ambiguous": [],
                "blocked": [{"code": "PUBLICATION_COHORT_NOT_FOUND", "cohort_id": cohort_id}],
                "missing": [], "unauthorized_paths": [], "cohort": None,
                "cohort_id": cohort_id, "drift_inputs": ["cohort identity"],
                "next_authorized_action": "RECONCILE_PUBLICATION_COHORT_AUTHORITY", "read_only": True,
            }
        if any(cohort.get(key) != expected for key, expected in (
            ("cohort_id", cohort_id), ("mission_id", mission),
            ("wop_id", wop_id), ("repository_id", projection.get("repository_id")),
        )):
            return {
                "result": "FAIL", "mission_id": mission, "wop_id": wop_id,
                "candidate_sources": [], "candidate_paths": [], "candidate_traceability": [],
                "candidate_digest": None, "classification_digest": None,
                "already_published": [], "historical_sources": [], "already_published_sources": [],
                "excluded_paths": [], "excluded_sources": [], "ambiguous": [],
                "blocked": [{"code": "PUBLICATION_COHORT_IDENTITY_MISMATCH", "cohort_id": cohort_id}],
                "missing": [], "unauthorized_paths": [], "cohort": cohort,
                "cohort_id": cohort_id, "drift_inputs": ["cohort identity"],
                "next_authorized_action": "RECONCILE_PUBLICATION_COHORT_AUTHORITY", "read_only": True,
            }
        member_ids = set(cohort.get("source_ids") or [])
        bound_member_ids = member_ids
        persisted_members = cohort.get("members") or []
        persisted_member_ids = {member.get("source_id") for member in persisted_members}
        persisted_member_digest = digest([
            {"source_id": member.get("source_id"), "source_path": member.get("source_path"),
             "source_type": member.get("source_type"), "mission_id": member.get("mission_id"),
             "wop_id": member.get("wop_id"), "qualification_state": member.get("qualification_state"),
             "publication_state": member.get("publication_state"), "context_digest": member.get("context_digest"),
             "dependency_relationship": member.get("dependency_relationship")}
            for member in sorted(persisted_members, key=lambda item: item.get("source_id") or "")
        ])
        member_records = {record.get("source_id"): record for record in records if record.get("source_id") in member_ids}
        drift_inputs: list[str] = []
        if persisted_member_ids != member_ids or persisted_member_digest != cohort.get("source_digest"):
            drift_inputs.append("cohort identity/membership digest")
        for member in cohort.get("members") or []:
            current = member_records.get(member.get("source_id"))
            if current is None:
                replacement = next((record for record in records if record.get("source_path") == member.get("source_path")), None)
                drift_inputs.append(f"cohort member {member.get('source_path')}" if replacement is None else f"cohort member manifest {member.get('source_path')}")
                continue
            if current.get("qualification_state") != member.get("qualification_state"):
                drift_inputs.append(f"qualification state {member.get('source_path')}")
            if current.get("publication_state") != member.get("publication_state"):
                drift_inputs.append(f"publication state {member.get('source_path')}")
            if current.get("context_digest") != member.get("context_digest"):
                drift_inputs.append(f"source/context digest {member.get('source_path')}")
        live_member_digest = digest([
            {"source_id": record["source_id"], "source_path": record["source_path"],
             "source_type": record.get("source_type"), "mission_id": record.get("mission_id"),
             "wop_id": record.get("wop_id"), "qualification_state": record.get("qualification_state"),
             "publication_state": record.get("publication_state"), "context_digest": record.get("context_digest"),
             "dependency_relationship": record.get("dependency_relationship")}
            for record in sorted(member_records.values(), key=lambda item: item["source_id"])
        ])
        if live_member_digest != cohort.get("source_digest"):
            drift_inputs.append("cohort source membership/qualification digest")
        if drift_inputs:
            return {
                "result": "FAIL", "mission_id": mission, "wop_id": wop_id,
                "candidate_sources": [member_records[key] for key in sorted(member_records)],
                "candidate_paths": [], "candidate_traceability": [], "candidate_digest": None,
                "classification_digest": live_member_digest, "candidate_authority_digest": live_member_digest,
                "already_published": [], "historical_sources": [], "already_published_sources": [],
                "excluded_paths": [], "excluded_sources": [], "ambiguous": [],
                "blocked": [{"code": "STALE_CLASSIFICATION", "reason": "bound publication cohort member authority changed", "inputs": drift_inputs}],
                "missing": [], "unauthorized_paths": [], "cohort": cohort, "cohort_id": cohort_id,
                "drift_inputs": sorted(set(drift_inputs)),
                "next_authorized_action": "REPREPARE_PUBLICATION_TRANSACTION", "read_only": True,
            }
        qualified = [member_records[source_id] for source_id in sorted(member_ids) if source_id in member_records]
    elif not manifest:
        from scripts.lib.emp import publication_cohort

        cohort = publication_cohort.resolve_for_candidate(
            repository,
            mission,
            runtime_root=runtime_root,
            lifecycle_projection=live,
        )
        if cohort and cohort.get("result") != "PASS":
            return {
                "result": "FAIL", "mission_id": mission, "wop_id": wop_id,
                "repository": projection, "candidate_sources": [], "all_sources": records,
                "candidate_paths": [], "candidate_traceability": [],
                "candidate_digest": None, "classification_digest": None,
                "already_published": [], "historical_sources": [],
                "already_published_sources": [], "excluded_paths": [],
                "excluded_sources": [], "ambiguous": [], "blocked": cohort.get("blockers", []),
                "missing": [], "unauthorized_paths": [], "cohort": cohort,
                "next_authorized_action": cohort.get("next_authorized_action", "RECONCILE_PUBLICATION_COHORT_AUTHORITY"),
                "read_only": True,
            }
    if cohort:
        members = set(cohort.get("source_ids", []))
        if not bound_cohort:
            excluded_qualified = [record for record in qualified if record.get("source_id") not in members]
            qualified = [record for record in qualified if record.get("source_id") in members]
        else:
            excluded_qualified = [record for record in records if record.get("publication_state") == "QUALIFIED_UNPUBLISHED" and record.get("source_id") not in members]
    else:
        excluded_qualified = []
    authority_records = [record for record in records if record.get("source_id") in bound_member_ids] if bound_cohort else records
    blocked_sources = [record for record in authority_records if record["publication_state"] in {"BLOCKED", "UNKNOWN"}]
    historical_sources = [record for record in authority_records if record["publication_state"] == "HISTORICAL_ONLY"]
    published_sources = [record for record in authority_records if record["publication_state"] == "ALREADY_PUBLISHED"]
    if blocked_sources:
        return {"result": "FAIL", "mission_id": mission, "wop_id": wop_id, "repository": projection, "candidate_sources": qualified, "all_sources": records, "excluded_sources": excluded_qualified, "candidate_paths": [], "blocked": [{"code": "QUALIFICATION_OR_PUBLICATION_STATE_UNRESOLVED", "source": item["source_path"], "reason": item["qualification_reason"] + "; " + item["publication_reason"]} for item in blocked_sources], "ambiguous": [], "missing": [], "already_published": [], "cohort": cohort, "next_authorized_action": "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY", "read_only": True}
    path_sources: dict[str, list[dict[str, Any]]] = {}
    for source in qualified:
        for path in source["candidate_paths"]:
            path_sources.setdefault(path, []).append(source)
    missing_dependencies = []
    qualified_keys = {key for source in qualified for key in (source["source_path"], source["source_id"], *source["candidate_paths"])}
    for source in qualified:
        for dependency in source.get("dependencies", []):
            if dependency not in qualified_keys:
                missing_dependencies.append({"source": source["source_path"], "dependency": dependency})
    if missing_dependencies:
        return {"result": "FAIL", "mission_id": mission, "wop_id": wop_id, "repository": projection, "candidate_sources": qualified, "all_sources": records, "excluded_sources": excluded_qualified, "candidate_paths": [], "blocked": [{"code": "MISSING_DEPENDENCY", **item} for item in missing_dependencies], "ambiguous": [], "missing": [], "already_published": [], "cohort": cohort, "next_authorized_action": "RESOLVE_PUBLICATION_DEPENDENCY", "read_only": True}
    raw_paths = sorted(path_sources)
    missing = sorted(path for path in raw_paths if not (repository / path).is_file())
    already_published = sorted(path for path in raw_paths if path not in missing and _path_publication_state(repository, path, projection["head"]) == "ALREADY_PUBLISHED")
    candidate_paths = sorted(path for path in raw_paths if path not in missing and path not in already_published)
    ambiguous = []
    for path, sources in path_sources.items():
        if path not in candidate_paths or len(sources) <= 1:
            continue
        cohorts = {source.get("publication_cohort", "") for source in sources}
        intents = {source.get("candidate_intent", "") for source in sources if source.get("candidate_intent")}
        cohort_authorized = bool(cohort and all(source.get("source_id") in set(cohort.get("source_ids", [])) for source in sources))
        if not cohort_authorized and (
            len({source["wop_id"] for source in sources}) > 1
            or len(intents) > 1
            or len(cohorts) != 1
            or "" in cohorts
        ):
            ambiguous.append({
                "path": path,
                "sources": [source["source_path"] for source in sources],
                "publication_cohorts": sorted(cohorts),
                "candidate_intents": sorted(intents),
                "reason": "overlapping current candidate claims require one explicit shared publication cohort",
            })
    if ambiguous:
        return {"result": "FAIL", "mission_id": mission, "wop_id": wop_id, "repository": projection, "candidate_sources": qualified, "all_sources": records, "excluded_sources": excluded_qualified, "candidate_paths": [], "blocked": [], "ambiguous": ambiguous, "missing": [], "already_published": [], "cohort": cohort, "next_authorized_action": "RECONCILE_PUBLICATION_CANDIDATE_AUTHORITY", "read_only": True}
    if cohort:
        cohort = dict(cohort)
        cohort["shared_path_count"] = sum(1 for sources in path_sources.values() if len(sources) > 1)
        cohort["ambiguous_path_count"] = len(ambiguous)
        cohort["blocked_path_count"] = 0
        cohort["candidate_authority_state"] = "RESOLVED"
    traceability = [{"path": path, "sources": [{"source": source["source_path"], "source_id": source["source_id"], "authority": source["authority"]} for source in path_sources[path]], "classification": "MISSION_CANDIDATE", "selection_reason": "qualified current mission/WOP publication manifest authorized by source-level cohort" if cohort else "qualified current mission/WOP publication manifest"} for path in candidate_paths]
    candidate_digest = digest([{ "path": item["path"], "sha256": hashlib.sha256((repository / item["path"]).read_bytes()).hexdigest() } for item in traceability]) if candidate_paths else None
    authority_records = [record for record in records if record.get("source_id") in bound_member_ids] if bound_cohort else records
    source_digest = digest([{"source_id": source["source_id"], "source_path": source["source_path"], "classification": source["publication_state"], "context_digest": source["context_digest"]} for source in authority_records])
    result = "PASS" if candidate_paths and not missing else "FAIL"
    return {
        "result": result, "mission_id": mission, "wop_id": wop_id, "repository": projection,
        "mission_projection": {key: live.get(key) for key in ("mission_id", "wop_id", "submission_id", "admission_id", "bootstrap_id", "lifecycle_state", "next_authorized_action")},
        "candidate_sources": qualified, "all_sources": records, "excluded_sources": excluded_qualified, "candidate_paths": candidate_paths,
        "candidate_traceability": traceability, "candidate_digest": candidate_digest, "classification_digest": source_digest,
        "already_published": already_published, "historical_sources": historical_sources, "already_published_sources": published_sources,
        "excluded_paths": sorted(set(raw_paths) - set(candidate_paths)), "ambiguous": ambiguous, "blocked": [], "missing": missing,
        "unauthorized_paths": [], "unrelated_dirty_count": len(set(projection.get("unstaged_paths", [])) | set(projection.get("untracked_paths", [])) - set(candidate_paths)),
        "cohort": cohort,
        "authority": {"type": "LIVE_PUBLICATION_COHORT_SOURCE_AUTHORITY" if cohort else "LIVE_MISSION_WOP_QUALIFIED_EVIDENCE", "mission_id": mission, "wop_id": wop_id, "source_digest": source_digest, "cohort_id": cohort.get("cohort_id") if cohort else None},
        "candidate_authority_digest": source_digest,
        "cohort_id": cohort.get("cohort_id") if cohort else None,
        "drift_inputs": [],
        "next_authorized_action": "PREPARE_PUBLICATION_CANDIDATE" if result == "PASS" else "RESOLVE_PUBLICATION_CANDIDATE_AUTHORITY", "read_only": True,
    }
