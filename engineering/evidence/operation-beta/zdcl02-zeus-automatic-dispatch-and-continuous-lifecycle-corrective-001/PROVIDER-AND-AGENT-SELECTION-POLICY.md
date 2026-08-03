# Provider and Agent Selection Policy

Selection is provider-neutral and uses the existing registry’s `active`,
`qualification_status`, and `repository_access_scope` fields. Qualified
agents are ordered by `agent_id`; an empty registry returns
`EXECUTION_AGENT_UNAVAILABLE`.
