# PowerAssist Security, PII and Data Retention

## 1. Purpose

PowerAssist provides information about Nigerian electricity distribution, tariffs, electricity regulations, and appliance energy consumption. This document describes the project's basic security and privacy safeguards.

## 2. Data Minimization

- Collect only the information needed to answer electricity-related questions.
- Do not request passwords, API keys, bank details, government identification numbers, or other unnecessary personal information.
- Avoid storing personal identifiers in questions, evaluation datasets, and application logs.
- Use synthetic or anonymized data for development and testing where practical.

## 3. Secrets Management

- Store local development secrets in `.env`, which must remain excluded from Git.
- Never hardcode API keys, passwords, or connection strings in source code.
- Store Azure application secrets in Azure Key Vault.
- Use managed identity for identity-based access to supported Azure resources.
- Verify runtime secret retrieval and restrict access to authorized identities and administrators.

## 4. Logging and Monitoring

- Record operational events, tool names, errors, and request latency where appropriate.
- Do not log API keys, authorization headers, full request bodies, or sensitive tool arguments.
- Return generic error messages to users while keeping necessary diagnostic details in protected monitoring systems.
- Restrict access to logs and monitoring data.
- Application Insights telemetry transmission has been verified through successful ingestion responses.

## 5. Data Retention and Deletion

- Do not intentionally persist chat messages beyond what is required to process the request unless a documented feature requires it.
- Review retention settings for the database, hosting platform, and monitoring service.
- Delete expired logs and test data according to the applicable retention policy.
- Review uploaded documents and indexed content periodically; remove content when it is no longer needed or when deletion is authorized.

**Current telemetry retention:** Application Insights is configured to retain telemetry for 90 days. Verify the resource's effective retention setting before production use.

**Proposed policy:** Consider reducing telemetry retention to 30 days if appropriate for troubleshooting and security monitoring. This change is not yet implemented.

## 6. Access Control

- Apply least-privilege access to application resources, databases, secrets, and telemetry.
- Use managed identity for supported Azure resource access instead of storing long-lived credentials in application configuration.
- Separate development and production configuration.
- Review access permissions periodically.

## 7. Guardrails and Validation

- Restrict the agent to Nigerian electricity information, energy estimation, distribution, tariffs, and relevant documents.
- Validate energy calculation inputs and structured lookup parameters.
- Limit agent tool calls per request and log tool execution without logging sensitive arguments.
- Test expected refusals, invalid inputs, and tool failures.

## 8. Privacy and Compliance

This document describes intended technical safeguards; it does not establish legal compliance. Before production use, review applicable Nigerian data protection requirements, contractual obligations, and other laws relevant to the users and data being processed.

## 9. Implementation Status

| Control | Status |
|---|---|
| Input validation and tool-level tests | Implemented and tested |
| Basic out-of-scope guardrail | Implemented and tested |
| Tool-call limit | Implemented and tested |
| Local secret exclusion from Git | Configured |
| Azure secrets stored in Key Vault | Verified |
| Managed identity and Key Vault permissions | Configured |
| Application runtime retrieval of Key Vault secrets | Pending verification |
| Application Insights integration | Configured; ingestion verified |
| Telemetry retention | 90 days; verify effective resource setting |
| 30-day telemetry retention policy | Proposed, not implemented |