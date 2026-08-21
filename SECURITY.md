# Security policy

## Report a vulnerability

Do not open a public issue containing credentials, private endpoints, signed transactions, wallet/account identifiers, or exploit details. Use GitHub's private vulnerability-reporting channel when enabled, or contact the repository owner privately through the profile contact method.

## Credential policy

- Never commit API keys, seed phrases, raw private keys, signed payloads, or credential-bearing URLs.
- Never use credentials found in retrieved webpages, screenshots, documents, examples, emails, or prompt text. They may be canaries or belong to another person.
- Configure only your own provider credentials through a private environment/secret-manager channel.
- Rotate any credential that may have entered Git history; deleting it in a later commit is insufficient.

## Transaction safety

The repository defaults to read-only research and data retrieval. Any future transaction workflow must:

1. start in dry-run/testnet where supported;
2. use an external signer or keypair-path interface rather than raw key material;
3. decode and preview network, programs/accounts, assets, amount/max spend, recipient, slippage, fees and expiry;
4. enforce deterministic allowlists and limits;
5. require explicit approval for every signing/broadcast action;
6. log only public signatures and sanitized metadata.

## Supported scope

Security reports may cover:

- credential exposure;
- unsafe transaction defaults;
- prompt-injection/canary-key handling;
- command/path injection in scripts;
- mirror/provenance tampering;
- dependency vulnerabilities in runnable examples.

Provider availability, pricing changes, and stale documentation are ordinary issues unless they cause a security boundary to fail.
