# Slide Outline: Secure File Storage & Sharing MVP

## Slide 1 — Title
- Secure File Storage & Sharing MVP
- Your Name • Course • Date

## Slide 2 — Problem
- Organizations share sensitive documents across insecure platforms
- Need encryption, access control, and auditability

## Slide 3 — Solution Overview
- Provider-agnostic MVP (free-path by default)
- Encrypted storage, IAM-like access, time-limited sharing, and audit logs

## Slide 4 — Architecture (High Level)
- Data plane: local storage backend (default) or AWS S3
- Security: encryption at rest, TLS in transit, API key-based access
- Sharing: expiring tokens / signed URLs
- Audit: persistent logs to cloud-like sink

## Slide 5 — Data Model (MVP)
- DataItem, ShareToken, AccessLog
- Key fields for each (id, bucketKey, expiresAt, scope, etc.)

## Slide 6 — MVP Deliverables
- Encrypted data storage
- Access control management
- Secure sharing mechanism
- Audit logs and reports

## Slide 7 — How It Works (Flow)
- Upload: encrypts and stores data
- Share: creates a token with expiry
- Access: token validates and decrypts
- Audit: events logged

## Slide 8 — Running It Locally
- Prereqs, installation steps, and how to run the API server
- curl examples for upload, share, and download

## Slide 9 — Free Path & Cloud Path</n+>
- Default local storage; can switch to AWS/GCP/Azure
- Minimal changes to backend for cloud switch

## Slide 10 — Demo Script
- Step-by-step sequence to showcase in class
- Expected outcomes and quick Q&A prompts

## Slide 11 — Security Considerations
- Encryption, access controls, token expiry, and audits
- What’s in scope for MVP vs. future work

## Slide 12 — Roadmap (Future Enhancements)
- Real revocation, multi-region, stronger threat modeling
- UI, automated tests, CI/CD
