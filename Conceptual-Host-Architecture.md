# Conceptual Engineering Platform Host & Topology Architecture

**Status:** Planning — Pre-Specification
**Architecture Workstream:** Workstream 1 — Capability Architecture
**Current Gate:** Gate 1.4 — Capability Constraints and Profiles
**Normative Authority:** None

---

# 1. Purpose

This document defines the evolving conceptual architecture for Engineering Hosts, Host capabilities, capability constraints, Service requirements, Service Placement, and derived Platform topology.

It is non-normative.

Its purpose is to establish a coherent architectural model before controlled specification drafting or implementation.

The architecture defines the conceptual relationships among:

* Engineering Assets;
* Engineering Hosts;
* Host identities;
* capabilities;
* capability contracts;
* capability qualifications;
* qualification scope;
* constraints;
* capability profiles;
* Platform Services;
* Service Instances;
* Service requirements;
* Service Placements;
* platform relationships;
* derived topology.

---

# 2. Architectural Vision

The Engineering Platform is a logical system composed of qualified Engineering Hosts that provide capabilities consumed by Platform Services.

Services should declare what they require rather than naming the machine on which they must run.

Hosts should advertise evidence-backed capabilities rather than fixed architectural roles.

Service Placement should evaluate:

```text
required capabilities
        +
capability dependencies
        +
qualification scope
        +
quantitative constraints
        +
qualitative constraints
        +
required relationships
        +
prohibited conditions
        +
trust requirements
        +
Placement policy
```

The architecture must support:

* one Host or many Hosts;
* physical and virtual execution environments;
* heterogeneous hardware;
* Host replacement;
* Service migration;
* restricted and degraded operation;
* future distributed Engineering Platform Services;
* explainable Placement decisions.

---

# 3. Guiding Principles

## 3.1 Stable Identity

Persistent engineering subjects require stable identities independent of mutable operational properties.

The following may change without changing Host identity:

* hostname;
* IP address;
* network interface;
* storage configuration;
* operating-system version;
* physical location;
* installed Services;
* display name.

---

## 3.2 Explicit Relationships

Platform relationships are engineering facts.

Topology should be derived from those relationships rather than embedded in:

* names;
* directory paths;
* diagrams;
* hardware descriptions;
* scripts;
* deployment notes.

---

## 3.3 Capability-Oriented Design

Hosts advertise qualified capabilities.

Services declare capability requirements.

Placement evaluates capability satisfaction together with constraints, trust, and relationships.

Hardware class alone does not establish fitness.

---

## 3.4 Separation of Authority

```text
Capability does not imply authority.

Qualification does not imply authorization.

Registration does not imply qualification.

Discovery does not imply admission.

Assignment does not imply activation.

Activation does not imply information ownership.

Reachability does not imply trust.

Profile satisfaction does not imply Placement approval.
```

---

## 3.5 Evidence-Based Qualification

A capability is qualified only through evidence appropriate to its contract and scope.

Evidence may include:

* inspection;
* configuration validation;
* functional testing;
* failure testing;
* recovery testing;
* security validation;
* performance measurement;
* persistence verification;
* operational observation.

---

## 3.6 Derived Topology

Topology is a representation of authoritative objects and relationships.

A topology view does not independently own:

* identity;
* authority;
* qualification;
* Service Placement;
* synchronization state;
* data ownership;
* operational truth.

---

## 3.7 Explicit Unknowns

Unknown, unavailable, or unobserved values must not be silently treated as satisfying requirements.

The architecture must distinguish:

```text
known and satisfied
known and unsatisfied
unknown
not applicable
not observed
conflicting evidence
```

---

# 4. Core Architectural Model

```text
Engineering Asset
        │
        │ provides or supports
        ▼
Engineering Host
        │
        ├── stable identity
        ├── operational condition
        ├── trust bindings
        ├── qualification records
        └── qualified capabilities
                │
                ├── contract version
                ├── evidence
                ├── scope
                ├── measured attributes
                └── limitations
                        │
                        │ evaluated against
                        ▼
                Service Requirements
                        │
                        ├── required capabilities
                        ├── alternative groups
                        ├── constraints
                        ├── required relationships
                        ├── prohibited conditions
                        └── trust requirements
                                │
                                ▼
                        Service Placement
                                │
                                ▼
                        Derived Platform Topology
```

---

# 5. Engineering Asset

An Engineering Asset is a managed physical resource.

Examples include:

* workstation;
* Raspberry Pi;
* physical server;
* storage appliance;
* networking device;
* external storage device;
* thin-client terminal;
* printer;
* diagnostic interface.

Asset ownership includes:

* physical identity;
* manufacturer and model;
* serial number;
* procurement;
* condition;
* maintenance;
* hardware lifecycle;
* retirement;
* physical qualification.

An Asset is not automatically an Engineering Host.

An Asset may:

* provide one Host;
* provide multiple virtual Hosts;
* support another Host;
* contain storage consumed by a Host;
* participate without executing Platform Services.

---

# 6. Engineering Host

An Engineering Host is a bounded execution environment capable of participating in the Engineering Platform.

Examples include:

* physical engineering workstation;
* Raspberry Pi operating environment;
* physical server;
* virtual machine;
* container host;
* thin-client environment;
* Service appliance;
* future cloud execution environment.

A Host owns or references:

* stable Host identity;
* names and aliases;
* observed environment;
* operational condition;
* trust bindings;
* capability declarations;
* capability qualifications;
* Service Placement relationships;
* lifecycle history.

A Host does not own:

* physical Asset lifecycle;
* Platform Service behavior;
* engineering work authorization;
* governance authority;
* Service-specific information authority;
* global operational truth owned by EOS.

---

# 7. Host Identity

A Host requires a stable identity independent of its current hostname.

The provisional form is:

```text
HOST-000001
```

Host identity is distinct from:

* `asset_id`;
* hostname;
* DNS name;
* IP address;
* MAC address;
* SSH alias;
* SSH key;
* operating-system installation identifier;
* Service identity;
* process identity;
* container runtime identifier.

Host identifiers must not be reused after retirement.

Historical names and bindings should remain discoverable.

---

# 8. Capability Definition

A Host Capability is a defined engineering function or property that an Engineering Host may be qualified to provide.

Capabilities describe Host fitness.

They do not determine:

* who may use the capability;
* which mission may invoke it;
* which Service currently consumes it;
* whether the Host is currently online;
* whether the Host owns authoritative information;
* whether Placement has been approved.

---

# 9. Capability Taxonomy

Capabilities are organized into seven conceptual categories:

```text
Host Capabilities
│
├── Interaction
├── Execution
├── Service Hosting
├── Persistence
├── Connectivity
├── Platform Integration
└── Specialized Compute
```

The categories organize the vocabulary.

They are metadata rather than capability identifier namespaces.

---

# 10. Provisional Capability Vocabulary

## 10.1 Interaction

```text
interactive-operation
local-user-interface
remote-interactive-access
mobile-operator-endpoint
```

## 10.2 Execution

```text
controlled-command-execution
engineering-workload-execution
isolated-execution
scheduled-execution
long-running-execution
```

## 10.3 Service Hosting

```text
persistent-service-hosting
service-supervision
host-native-supervision
always-on-operation
service-isolation
service-health-reporting
```

## 10.4 Persistence

```text
durable-local-storage
qualified-authoritative-storage
backup-capable-storage
recoverable-storage
removable-storage-support
```

## 10.5 Connectivity

```text
authenticated-network-listener
authenticated-network-client
local-network-participation
outbound-network-access
internet-service-access
external-message-delivery
time-synchronization
```

## 10.6 Platform Integration

```text
repository-access
repository-working-copy
platform-state-consumption
platform-state-publication
engineering-record-consumption
engineering-record-publication
platform-observation
platform-synchronization
peripheral-device-access
```

## 10.7 Specialized Compute

```text
high-memory-compute
parallel-cpu-compute
gpu-compute
ai-inference
ai-training
hardware-diagnostics
storage-qualification
```

---

# 11. Capability Dependency Model

Capabilities form a directed acyclic graph.

Supported relationship types are:

```text
requires
implies
alternative
conflicts_with
```

General capability inheritance is rejected.

The preferred model is:

```text
independent capability contracts
        +
explicit dependencies
        +
qualification scope
        +
constraints
```

Dependency satisfaction requires compatible contract versions and compatible scopes.

---

# 12. Constraint Definition

A Constraint is an explicit condition applied to:

* a capability qualification;
* a capability requirement;
* a Host;
* a relationship;
* a Service Placement;
* a prohibited condition;
* a profile.

Constraints refine meaning that cannot be expressed accurately through capability presence alone.

Examples include:

* minimum memory;
* storage capacity;
* latency;
* availability;
* processor architecture;
* network zone;
* physical location;
* trust domain;
* retention;
* recovery objective;
* power continuity;
* supported protocol;
* attached device identity.

---

# 13. Capability Versus Constraint

A concept should be modeled as a capability when it describes reusable Host behavior that can be independently qualified.

A concept should be modeled as a constraint when it limits, measures, selects, or scopes a capability or Placement.

## Capability Examples

```text
durable-local-storage
gpu-compute
remote-interactive-access
service-supervision
```

## Constraint Examples

```text
minimum_available_capacity_gb: 100
minimum_gpu_memory_gb: 12
maximum_latency_ms: 50
processor_architecture: x86_64
network_zone: engineering-private
```

Avoid creating Boolean capabilities for arbitrary thresholds.

Avoid:

```text
large-storage
fast-network
high-availability
modern-cpu
```

Prefer:

```yaml
capability_id: durable-local-storage
constraints:
  minimum_available_capacity_gb: 1000
```

---

# 14. Constraint Domains

The architecture defines six conceptual constraint domains:

1. Resource
2. Performance
3. Compatibility
4. Operational
5. Placement
6. Information and Trust

These domains organize constraint definitions.

They do not determine authority.

---

# 15. Resource Constraints

Resource constraints describe available or required capacity.

Examples include:

```text
memory_gb
available_storage_gb
cpu_logical_processors
cpu_physical_cores
gpu_memory_gb
network_bandwidth_mbps
battery_runtime_minutes
```

Example:

```yaml
constraint:
  field: memory_gb
  operator: greater_than_or_equal
  value: 16
  unit: GiB
```

Resource values should identify whether they are:

* installed;
* usable;
* available;
* reserved;
* allocatable;
* measured under load.

A Service requirement should normally use the value relevant to Placement.

For example:

```text
available memory
```

is usually more meaningful than:

```text
installed memory
```

---

# 16. Performance Constraints

Performance constraints describe measured or required behavior.

Examples include:

```text
maximum_latency_ms
minimum_throughput_mbps
minimum_iops
maximum_startup_seconds
maximum_recovery_seconds
minimum_events_per_second
minimum_inference_tokens_per_second
```

Performance constraints should identify:

* measurement method;
* workload;
* test conditions;
* evidence timestamp;
* acceptable variance;
* qualification scope.

A raw benchmark without defined conditions must not establish a general performance qualification.

---

# 17. Compatibility Constraints

Compatibility constraints describe required or supported environments.

Examples include:

```text
processor_architecture
operating_system_family
operating_system_version
filesystem_type
container_runtime
model_runtime
protocol
api_contract_version
device_class
device_identifier
```

Example:

```yaml
constraint:
  field: processor_architecture
  operator: in
  value:
    - x86_64
    - aarch64
```

Compatibility constraints should not duplicate Service implementation unnecessarily.

A Service should declare a compatibility requirement only when the implementation genuinely depends on it.

---

# 18. Operational Constraints

Operational constraints describe expected operating conditions.

Examples include:

```text
availability_target
unattended_restart_required
maximum_maintenance_window
time_accuracy_seconds
power_continuity_required
minimum_retention_days
recovery_point_objective
recovery_time_objective
```

Example:

```yaml
constraint:
  field: unattended_restart
  operator: equals
  value: true
```

Operational constraints must remain separate from current health observations.

Example:

```text
availability target: 99%
```

is a requirement.

```text
Host currently online
```

is an observation.

---

# 19. Placement Constraints

Placement constraints govern where and how a Service Instance may be placed.

Examples include:

```text
required_host_id
excluded_host_id
required_location
excluded_location
required_failure_domain
anti_affinity
co_location
maximum_instances_per_host
exclusive_device_access
network_zone
```

Example:

```yaml
placement_constraints:
  anti_affinity:
    - notification-primary
  maximum_instances_per_host: 1
```

Placement constraints do not become Host capabilities.

---

# 20. Information and Trust Constraints

Information and trust constraints describe data-handling or trust boundaries that affect Placement.

Examples include:

```text
trust_domain
data_classification
authoritative_data_allowed
external_egress_allowed
encryption_at_rest_required
encryption_in_transit_required
approved_identity_provider
credential_storage_class
```

Example:

```yaml
trust_constraints:
  trust_domain: engineering-private
  authoritative_data_allowed: true
  external_egress_allowed: false
```

These constraints reference trust or policy authorities.

They do not grant trust or authority themselves.

---

# 21. Constraint Data Types

The common constraint model should support:

```text
boolean
integer
decimal
string
enumeration
duration
timestamp
version
quantity-with-unit
identifier-reference
set
range
```

Free-form text should not be used for deterministic matching.

Free-form notes may supplement a constraint but must not replace its machine-evaluable value.

---

# 22. Constraint Operators

The initial common operator set is:

```text
equals
not_equals
greater_than
greater_than_or_equal
less_than
less_than_or_equal
in
not_in
contains
contains_all
contains_any
matches_version
within_range
exists
not_exists
```

Operators must be valid for the applicable data type.

Examples:

```yaml
- field: memory_gb
  operator: greater_than_or_equal
  value: 16
  unit: GiB

- field: processor_architecture
  operator: in
  value:
    - x86_64
    - aarch64

- field: internet_egress
  operator: equals
  value: false
```

---

# 23. Unit Model

Quantitative constraints require normalized units.

The architecture should prefer explicit, unambiguous units.

Examples include:

```text
bytes
KiB
MiB
GiB
TiB
milliseconds
seconds
minutes
hours
days
bps
Kbps
Mbps
Gbps
IOPS
watts
volts
degrees_celsius
percent
```

The future specification must define:

* canonical storage units;
* conversion behavior;
* precision;
* rounding;
* overflow behavior;
* comparison tolerance.

Values without units must not be compared when the field requires a unit.

---

# 24. Constraint Ownership

Constraint definitions have different owners.

| Constraint type                     | Authoritative owner                            |
| ----------------------------------- | ---------------------------------------------- |
| Common field and operator semantics | Host & Topology Architecture                   |
| Service requirement values          | Applicable Service specification               |
| Host measured values                | Host qualification or observation record       |
| Trust-domain definitions            | Trust Architecture or applicable policy        |
| Asset-specific properties           | Hardware Architecture or Asset record          |
| Current operational state           | EOS                                            |
| Placement policy                    | Applicable placement authority                 |
| Evidence method                     | Qualification procedure or capability contract |

The Host Architecture defines evaluation semantics without absorbing all source facts.

---

# 25. Qualification Scope

A Capability Qualification applies only within an explicit scope.

Scope defines the boundary within which the qualification is valid.

Possible scope dimensions include:

```text
host
filesystem
mount point
network interface
network zone
service account
runtime
container
virtual machine
device
device class
repository
data class
protocol
endpoint
operator interface
time window
```

Example:

```yaml
qualification:
  host_id: HOST-000001
  capability_id: durable-local-storage
  contract_version: 1
  state: Qualified

  scope:
    filesystem_path: /data/engineering
    filesystem_type: ext4
    authoritative_data_allowed: false

  measured_attributes:
    available_capacity_gb: 240
```

The qualification does not automatically apply to:

```text
/
 /tmp
removable storage
network-mounted storage
another Host
```

---

# 26. Scope Compatibility

A requirement is satisfied only when the qualification scope covers the requested scope.

Example requirement:

```yaml
required_capability:
  capability_id: durable-local-storage
  scope:
    filesystem_path: /var/lib/notification-service
```

Qualification:

```yaml
scope:
  filesystem_path: /data/engineering
```

This qualification does not satisfy the requirement unless the Service path is actually provided within the qualified storage scope.

Scope matching may use:

* exact identity;
* containment;
* membership;
* compatible class;
* explicitly declared equivalence.

Scope must never be broadened by assumption.

---

# 27. Scope Inheritance

General scope inheritance is rejected.

A broad Host-level qualification may apply to subordinate resources only when the capability contract explicitly permits it.

Example:

```text
time-synchronization
```

may reasonably apply Host-wide.

Example:

```text
peripheral-device-access
```

must identify the applicable device or device class.

The capability contract must define its permitted scope model.

---

# 28. Requirement Strength

Service requirements may use four strength levels:

1. Required
2. Optional
3. Preferred
4. Prohibited

## Required

The Placement cannot qualify unless the requirement is satisfied.

## Optional

The capability or constraint may be used if present but does not affect eligibility.

## Preferred

The requirement affects ranking or selection but not basic eligibility.

## Prohibited

The condition must not exist within the applicable Placement scope.

Example:

```yaml
requirements:
  required_capabilities:
    - persistent-service-hosting

  preferred_capabilities:
    - always-on-operation

  optional_capabilities:
    - service-health-reporting

  prohibited_conditions:
    - external-internet-egress
```

---

# 29. Prohibited Conditions

A Prohibited Condition describes a state, property, relationship, or capability use that makes a Placement ineligible.

Examples include:

```text
external Internet egress
unapproved removable storage
unencrypted authoritative data
placement outside approved trust domain
co-location with conflicting Service
unqualified peripheral access
shared credential storage
```

Prohibited conditions may evaluate:

* Host properties;
* capability scopes;
* relationships;
* operational configuration;
* trust bindings;
* Placement combinations.

They should not be represented as inverse capabilities.

Avoid:

```text
no-internet
not-removable-storage
non-cloud
```

---

# 30. Alternative Requirement Groups

A Service may permit more than one way to satisfy a requirement.

Alternative groups support:

```text
any_of
all_of
one_of
at_least
at_most
```

## `any_of`

At least one member must be satisfied.

```yaml
any_of:
  - capability_id: host-native-supervision
  - capability_id: container-service-supervision
  - capability_id: appliance-service-supervision
```

## `all_of`

Every member must be satisfied.

```yaml
all_of:
  - capability_id: durable-local-storage
  - capability_id: time-synchronization
```

## `one_of`

Exactly one member must be selected.

This should be used sparingly because a Host may legitimately qualify for multiple alternatives.

## `at_least`

A minimum number of members must be satisfied.

```yaml
at_least:
  count: 2
  members:
    - capability_id: backup-capable-storage
    - capability_id: snapshot-capable-storage
    - capability_id: replication-capable-storage
```

## `at_most`

No more than a defined number may apply within the Placement scope.

This may be useful for mutually constrained mechanisms but is not a substitute for `conflicts_with`.

---

# 31. Alternative Group Evaluation

Alternative groups must define:

* member requirements;
* group operator;
* required count where applicable;
* scope;
* constraints;
* selected satisfaction path;
* evidence references.

A successful evaluation should explain which alternative satisfied the requirement.

Example:

```yaml
evaluation:
  group_id: recovery-mechanism
  result: Satisfied
  selected_member:
    capability_id: backup-capable-storage
  evidence:
    - QUAL-000145
```

---

# 32. Recovery Mechanism Model

Recoverable storage must be supported by at least one qualified recovery mechanism.

Candidate recovery capabilities include:

```text
backup-capable-storage
snapshot-capable-storage
replication-capable-storage
reconstructable-storage
```

The provisional recovery requirement is:

```yaml
profile:
  required_capabilities:
    - durable-local-storage

  alternative_groups:
    - group_id: recovery-mechanism
      any_of:
        - backup-capable-storage
        - snapshot-capable-storage
        - replication-capable-storage
        - reconstructable-storage
```

The exact recovery mechanism must satisfy Service-specific objectives such as:

* recovery-point objective;
* recovery-time objective;
* retention;
* independence from the source failure domain;
* integrity validation;
* restoration testing.

---

# 33. Recovery Vocabulary Refinement

Gate 1.4 adds the following provisional capabilities:

```text
snapshot-capable-storage
replication-capable-storage
reconstructable-storage
```

These are added because they represent distinct reusable Host or storage behaviors.

They do not automatically establish recoverability.

Recoverability is achieved only when:

```text
qualified durable storage
        +
qualified recovery mechanism
        +
Service-specific recovery constraints
        +
validated recovery evidence
```

---

# 34. Capability Profile Definition

A Capability Profile is a named, versioned, reusable requirement composition.

A profile may contain:

* required capabilities;
* preferred capabilities;
* optional capabilities;
* alternative groups;
* common constraints;
* required relationships;
* prohibited conditions.

Profiles improve reuse and readability.

Profiles do not represent Host identity or Host role.

---

# 35. Profile Example

```yaml
profile_id: persistent-platform-service
profile_version: 1

required_capabilities:
  - persistent-service-hosting
  - authenticated-network-listener
  - durable-local-storage
  - time-synchronization

preferred_capabilities:
  - always-on-operation
  - service-health-reporting

constraints:
  - field: unattended_restart
    operator: equals
    value: true
```

A Service may reference the profile and add Service-specific requirements.

```yaml
service_id: notification-service

uses_profiles:
  - profile_id: persistent-platform-service
    profile_version: 1

additional_required_capabilities:
  - external-message-delivery
```

---

# 36. Profiles Are Not Roles

A profile is not:

* a Host type;
* a deployment assignment;
* an authority grant;
* a Placement;
* an operational state;
* a fixed machine role.

A Host does not become a:

```text
persistent-platform-service-host
```

as an authoritative identity merely because it satisfies that profile.

The correct interpretation is:

```text
Host satisfies profile requirements
```

not:

```text
Host is assigned permanent profile role
```

---

# 37. Profile Composition

A profile may reference another profile when composition improves reuse.

Example:

```yaml
profile_id: recoverable-persistent-service
profile_version: 1

uses_profiles:
  - profile_id: persistent-platform-service
    profile_version: 1
  - profile_id: recoverable-storage
    profile_version: 1
```

Profile composition must be acyclic.

A profile must not silently weaken requirements inherited through composition.

---

# 38. Profile Conflict Resolution

When a Service combines profiles and additional requirements:

* required requirements accumulate;
* prohibited conditions accumulate;
* preferred requirements remain ranking inputs;
* optional requirements remain informational;
* stronger constraints override weaker constraints only when compatible;
* contradictory requirements cause the composition to be invalid.

Example conflict:

```text
Profile A:
  internet_egress_allowed: false

Profile B:
  internet_egress_required: true
```

The combination is invalid unless the scopes are distinct and explicitly represented.

---

# 39. Profile Versioning

A profile has a stable identifier and a separate version.

Example:

```yaml
profile_id: persistent-platform-service
profile_version: 1
```

A new version is required when the profile changes in a way that may affect:

* Host eligibility;
* Placement outcome;
* required capabilities;
* prohibited conditions;
* required relationships;
* constraint thresholds;
* alternative-group behavior.

Minor documentation clarification may retain the same profile version.

---

# 40. Profile Migration

When a profile version changes:

1. publish the new profile version;
2. identify Services referencing the prior version;
3. identify active Placements evaluated against the prior version;
4. evaluate compatibility;
5. requalify affected Placements where necessary;
6. migrate Service declarations;
7. retire the prior profile only after dependent Services have migrated.

Profile version changes must not silently alter active Placements.

---

# 41. Profile Ownership

The shared Host & Topology Architecture may own Platform-wide profiles.

Examples might include:

```text
persistent-platform-service
recoverable-storage
interactive-engineering-host
isolated-compute-service
```

A Service specification may own Service-specific profiles.

Example:

```text
notification-primary-instance
```

Service-specific profiles must not be promoted into the shared capability registry unless they demonstrate reusable Platform semantics.

---

# 42. Profile Registry

A future profile registry should record:

```yaml
profile_id: persistent-platform-service
profile_version: 1
status: Provisional
owner: Engineering Platform Host Architecture
description: Reusable requirements for persistent Platform Services
uses_profiles: []
required_capabilities: []
preferred_capabilities: []
optional_capabilities: []
alternative_groups: []
constraints: []
required_relationships: []
prohibited_conditions: []
```

The registry must validate:

* unique identifiers;
* version integrity;
* composition acyclicity;
* capability references;
* contract-version compatibility;
* constraint syntax;
* conflicting requirements;
* prohibited-condition consistency.

---

# 43. Missing-Value Semantics

A missing value is not equivalent to:

* zero;
* false;
* empty;
* unsupported;
* prohibited;
* satisfied.

The common evaluation states are:

```text
Known Satisfied
Known Unsatisfied
Unknown
Not Observed
Not Applicable
Conflicting Evidence
Stale
```

---

# 44. Missing-Value Evaluation Rules

## Required Requirement

A required constraint with an unknown or unobserved value is not satisfied.

Example:

```text
minimum_available_storage_gb: 100
observed value: Unknown
result: Unresolved
```

The Placement cannot qualify until the value is established or an explicit policy permits conditional qualification.

## Preferred Requirement

An unknown preferred value should not disqualify the Host.

It may reduce ranking confidence.

## Optional Requirement

An unknown optional value is informational.

## Prohibited Condition

An unknown prohibited condition should normally block qualification when safety, trust, or authoritative data is involved.

For lower-risk conditions, policy may permit a restricted result.

---

# 45. Stale Values

Measured attributes and observations require freshness metadata.

Example:

```yaml
measured_attribute:
  field: available_storage_gb
  value: 240
  observed_at: 2026-07-19T18:00:00-07:00
  valid_for: PT24H
```

After expiration, the value becomes:

```text
Stale
```

A stale value must not be treated as current unless the requirement explicitly permits it.

Static facts may use event-based invalidation rather than time-based expiration.

---

# 46. Conflicting Evidence

When evidence sources disagree, the result is:

```text
Conflicting Evidence
```

The architecture must not select the most favorable value silently.

Resolution may require:

* source-priority rules;
* reinspection;
* manual review;
* invalidation of stale evidence;
* qualification suspension.

The evaluation explanation must identify all conflicting sources.

---

# 47. Constraint Evaluation Result

A constraint evaluation should produce more than a Boolean.

Conceptual result:

```yaml
constraint_result:
  field: memory_gb
  operator: greater_than_or_equal
  required_value: 16
  observed_value: 32
  result: Satisfied
  source: QUAL-000101
  scope:
    host_id: HOST-000001
```

Possible results include:

```text
Satisfied
Unsatisfied
Unresolved
Not Applicable
Conflict
Stale
Error
```

---

# 48. Requirement Evaluation Result

A complete requirement evaluation should report:

```yaml
requirement_result:
  requirement_id: REQ-001
  result: Satisfied

  capability:
    capability_id: durable-local-storage
    contract_version: 1

  qualification:
    qualification_id: QUAL-000145
    state: Qualified

  scope_result: Satisfied

  constraint_results:
    - field: available_storage_gb
      result: Satisfied

  dependency_results:
    - capability_id: recoverable-storage
      result: Satisfied
```

This explainability is mandatory for future deterministic matching.

---

# 49. Candidate Shared Profiles

The following profiles are provisional architecture candidates.

## 49.1 Persistent Platform Service

```yaml
profile_id: persistent-platform-service

required_capabilities:
  - persistent-service-hosting
  - service-supervision
  - durable-local-storage
  - time-synchronization

preferred_capabilities:
  - always-on-operation
  - service-health-reporting
```

## 49.2 Recoverable Storage

```yaml
profile_id: recoverable-storage

required_capabilities:
  - durable-local-storage

alternative_groups:
  - group_id: recovery-mechanism
    any_of:
      - backup-capable-storage
      - snapshot-capable-storage
      - replication-capable-storage
      - reconstructable-storage
```

## 49.3 Interactive Engineering Environment

```yaml
profile_id: interactive-engineering-environment

required_capabilities:
  - interactive-operation
  - controlled-command-execution
  - engineering-workload-execution

preferred_capabilities:
  - remote-interactive-access
  - repository-working-copy
  - engineering-record-consumption
```

## 49.4 Isolated Compute Service

```yaml
profile_id: isolated-compute-service

required_capabilities:
  - isolated-execution
  - engineering-workload-execution

preferred_capabilities:
  - service-supervision
  - service-health-reporting
```

These profiles remain provisional and must be validated against actual Service specifications.

---

# 50. Candidate Service Requirement Structure

```yaml
service_id: example-service
service_contract_version: 1

uses_profiles:
  - profile_id: persistent-platform-service
    profile_version: 1

requirements:
  required_capabilities:
    - authenticated-network-listener

  preferred_capabilities:
    - always-on-operation

  optional_capabilities:
    - platform-observation

  alternative_groups:
    - group_id: delivery-path
      any_of:
        - external-message-delivery
        - engineering-record-publication

  quantitative_constraints:
    - field: available_storage_gb
      operator: greater_than_or_equal
      value: 100
      unit: GiB

  required_relationships:
    - relationship_type: backed_up_by

  prohibited_conditions:
    - field: external_egress_uncontrolled
      operator: equals
      value: true

  trust_constraints:
    trust_domain: engineering-private

  placement_constraints:
    unattended_restart: required
```

The structure remains provisional.

---

# 51. Candidate Host Qualification Structure

```yaml
qualification_id: QUAL-000145
host_id: HOST-000001

capability:
  capability_id: durable-local-storage
  contract_version: 1

state: Qualified

scope:
  filesystem_path: /data/engineering
  filesystem_type: ext4

measured_attributes:
  - field: available_storage_gb
    value: 240
    unit: GiB
    observed_at: 2026-07-19T18:00:00-07:00

limitations:
  authoritative_data_allowed: false

evidence:
  - evidence_id: EVID-000201
    type: functional-test
```

---

# 52. Constraint and Profile Validation Rules

A future registry or validator must reject:

* unknown constraint fields;
* incompatible operators;
* missing required units;
* invalid enumerations;
* unresolved capability references;
* profile dependency cycles;
* capability dependency cycles;
* contradictory required and prohibited conditions;
* incompatible profile versions;
* invalid scope expansion;
* silent use of stale values;
* free-form values where deterministic matching is required.

---

# 53. Capability Matching Inputs

Future Host matching must evaluate:

```text
required capability identities
        +
capability contract versions
        +
dependency closure
        +
qualification states
        +
qualification scopes
        +
profile expansion
        +
alternative-group resolution
        +
quantitative constraints
        +
qualitative constraints
        +
required relationships
        +
prohibited conditions
        +
trust requirements
        +
Placement policy
        +
evidence freshness
```

---

# 54. Matching Output Requirements

The matching result must explain:

* satisfied requirements;
* unmet requirements;
* selected alternatives;
* unresolved alternatives;
* incompatible contract versions;
* insufficient scope;
* expired qualifications;
* stale values;
* failed constraints;
* prohibited conditions;
* missing relationships;
* trust failures;
* profile expansion;
* ranking effects from preferred requirements.

The matching model itself remains Gate 1.5.

---

# 55. Platform Services

A Platform Service is a logical engineering function.

Examples include:

* Engineering Control;
* Checkpoint Service;
* Repository Service;
* Notification Service;
* Engineering Knowledge Repository;
* future Mission Orchestrator.

A Platform Service owns:

* logical Service behavior;
* information authority;
* Service requirements;
* Service-specific lifecycle;
* persistence obligations;
* client behavior;
* recovery semantics.

A Platform Service does not own generic Host capability or constraint semantics.

---

# 56. Service Instances

A Service Instance is a runtime realization of a Platform Service.

Example:

```yaml
service_id: notification-service
instance_id: notification-primary
```

A Service may have:

* primary instances;
* standby instances;
* development instances;
* migration instances;
* replicas;
* future active-active instances.

Instance identity remains independent of Host identity.

---

# 57. Service Placement

A Service Placement is the qualified relationship binding a Service Instance to an Engineering Host.

A Placement records or references:

* Service identity;
* Instance identity;
* Host identity;
* capability requirements;
* expanded profiles;
* dependency closure;
* Host qualifications;
* scope evaluations;
* constraint evaluations;
* selected alternatives;
* trust requirements;
* required relationships;
* prohibited conditions;
* Placement Qualification;
* lifecycle state;
* migration history;
* evidence.

Example:

```yaml
placement_id: PLC-000001
instance_id: notification-primary
host_id: HOST-000007
state: Proposed
```

---

# 58. Platform Relationships

Minimum relationship classes include:

## Asset and Host

```text
provides_host
hosted_by
depends_on_asset
```

## Host and Host

```text
communicates_with
synchronizes_with
observes
administers
depends_on_host
replaces_host
```

## Service and Instance

```text
has_instance
instance_of
```

## Instance and Host

```text
placed_on
hosts_instance
```

## Service Dependencies

```text
depends_on_service
consumes_service
publishes_to_service
```

## Persistence

```text
persists_to
replicates_to
backed_up_by
```

Topology views own no independent facts.

---

# 59. Ownership Model

| Concept                          | Authoritative owner                         |
| -------------------------------- | ------------------------------------------- |
| Physical Asset                   | Hardware Architecture and Asset record      |
| Host identity                    | Future Host architecture and registry       |
| Capability identity and contract | Host & Topology Architecture                |
| Capability dependency graph      | Host & Topology Architecture                |
| Common constraint semantics      | Host & Topology Architecture                |
| Shared capability profiles       | Host & Topology Architecture                |
| Service-specific profiles        | Applicable Service specification            |
| Capability Qualification         | Qualification record and evidence           |
| Platform Service                 | Applicable Service specification or catalog |
| Service requirements             | Applicable Service specification            |
| Service Instance                 | Applicable Service runtime or registry      |
| Service Placement semantics      | Host & Topology Architecture                |
| Current deployed baseline        | Infrastructure Baseline                     |
| Operational state                | EOS                                         |
| Engineering work state           | EMP Work Registry                           |
| Engineering authority            | Governance and active work authorization    |
| Topology view                    | Derived; owns no authoritative facts        |

---

# 60. Lifecycle Domains

## Host Lifecycle

```text
Discovered
Registered
Qualification Pending
Qualified
Restricted
Unavailable
Retired
```

## Capability Qualification Lifecycle

```text
Declared
Evidence Pending
Qualified
Restricted
Suspended
Expired
Revoked
Requalification Required
```

## Service Instance Lifecycle

```text
Declared
Provisioned
Configured
Qualified
Standby
Running
Degraded
Stopped
Failed
Retired
```

## Placement Lifecycle

```text
Proposed
Requirements Verified
Host Matched
Placement Qualified
Assigned
Activated
Suspended
Failed
Migrating
Released
Historical
```

Operational health, qualification, trust, and lifecycle remain independent dimensions.

---

# 61. Gate 1.4 Decisions

Gate 1.4 establishes the following planning decisions:

1. Constraints are separate from capabilities.
2. Constraints may apply to qualifications, requirements, Hosts, relationships, profiles, or Placements.
3. Constraint domains are Resource, Performance, Compatibility, Operational, Placement, and Information and Trust.
4. Constraints require typed, machine-evaluable values.
5. A common operator set is established for planning.
6. Quantitative values require explicit units.
7. Constraint ownership remains distributed among the applicable authorities.
8. Capability Qualifications require explicit scope.
9. Scope satisfaction must be evaluated explicitly.
10. General scope inheritance is rejected.
11. Service requirements may be Required, Optional, Preferred, or Prohibited.
12. Prohibited conditions remain distinct from inverse capabilities.
13. Alternative requirement groups support `any_of`, `all_of`, `one_of`, `at_least`, and `at_most`.
14. Alternative-group satisfaction must identify the selected path.
15. Recoverable storage requires at least one qualified recovery mechanism.
16. `snapshot-capable-storage`, `replication-capable-storage`, and `reconstructable-storage` are added provisionally.
17. Capability Profiles are named, versioned requirement compositions.
18. Profiles are not Host roles.
19. Profile composition must be acyclic.
20. Contradictory profile requirements invalidate the composition.
21. Breaking profile changes require a new version.
22. Profile changes must not silently alter active Placements.
23. Missing values do not satisfy required requirements.
24. Unknown prohibited conditions normally block safety- or trust-sensitive Placement.
25. Stale evidence must not be treated as current.
26. Conflicting evidence must be surfaced explicitly.
27. Constraint and requirement evaluations must be explainable.
28. Free-form text cannot replace deterministic constraint values.

---

# 62. Revised Persistence Vocabulary

Gate 1.4 refines the Persistence category to:

```text
durable-local-storage
qualified-authoritative-storage
backup-capable-storage
snapshot-capable-storage
replication-capable-storage
reconstructable-storage
recoverable-storage
removable-storage-support
```

`recoverable-storage` remains a composed qualification rather than proof that every recovery mechanism exists.

---

# 63. Open Design Areas

The following questions remain unresolved:

* What is the final canonical constraint registry?
* Which fields are Platform-wide?
* How are custom Service constraints registered?
* What is the exact unit normalization standard?
* How are floating-point tolerances handled?
* How are version ranges expressed?
* How are nested scopes represented?
* How are partial-scope matches scored?
* How are preferred requirements weighted?
* How are multiple eligible alternative paths ranked?
* How are restricted qualifications treated?
* How are operational observations combined with qualification records?
* What is the exact prohibited-condition evaluation policy?
* Which unknown conditions permit restricted Placement?
* How are relationship constraints represented?
* How are trust requirements resolved?
* How are profile deprecations represented?
* How are existing Placements reevaluated after profile changes?

---

# 64. Next Gate

Proceed to:

```text
Workstream 1
Gate 1.5 — Capability Matching
```

Gate 1.5 should define:

* requirement resolution;
* profile expansion;
* dependency expansion;
* version compatibility;
* qualification-state eligibility;
* scope matching;
* constraint evaluation;
* alternative-group resolution;
* relationship evaluation;
* prohibited-condition evaluation;
* trust input handling;
* preferred-requirement ranking;
* deterministic result states;
* explanation structure;
* failure classification;
* candidate Host comparison;
* Placement recommendation boundaries.

Gate 1.5 must ensure that matching recommends eligible Hosts but does not authorize Placement.

---

# 65. Maturity

```text
Repository archaeology: substantially complete

Host abstraction: established

Ownership boundaries: established

Runtime lifecycle: conceptually established

Identity model: conceptually established

Capability taxonomy: provisionally validated

Capability hierarchy: established for planning

Dependency semantics: established for planning

Constraint model: established for planning

Qualification scope model: established for planning

Capability profiles: established for planning

Capability matching: pending

Capability lifecycle integration: pending

Controlled specification: not authorized
```

