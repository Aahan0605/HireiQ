# Data Processing Agreement (DPA)

This Data Processing Agreement ("DPA") is entered into by and between:
1. **The Customer** (acting as "Data Controller"), and
2. **HireIQ** (acting as "Data Processor").

This DPA governs the processing of candidate and recruiter personal data in connection with the HireIQ Applicant Tracking System services under the Terms of Service.

---

## 1. Scope & Processing Details
- **Subject Matter**: Processing resume data, career profiles, and contact details of job applicants uploaded by Controller.
- **Duration**: Co-extensive with the active subscription term of the Controller.
- **Nature of Processing**: Structured parsing, scoring, anonymization, and comparison of candidates against job specifications.
- **Categories of Data**: Candidate names, email addresses, skills, work histories, locations, and social profile links.

---

## 2. Technical and Organizational Security Measures
Processor shall implement state-of-the-art security measures to protect candidate data against unauthorized access, disclosure, or loss, including:
- **AES-128 Column Encryption**: Symmetrical encryption of candidate PII (name, email) at rest.
- **Tenant Separation**: Strict database logical tenant separation ensuring no organization can access another organization's candidate or job tables.
- **Access Control**: Role-Based Access Control (RBAC) preventing unauthorized roles (e.g. viewers or hiring managers) from performing destructive operations.

---

## 3. Sub-Processors
Processor utilizes the following sub-processors for core service operations. Controller hereby grants general authorization for:
1. **Google Cloud / Gemini API**: For AI resume feature extraction and bias audit processing (all data is processed anonymously without passing candidate PII).
2. **Stripe Inc**: For payment capture and subscription management.
3. **Resend Inc**: For transactional email notifications and recruiter invitation emails.

---

## 4. GDPR & CCPA Compliance Assurances
- **Data Subject Rights**: Processor provides API endpoints to support Controller in fulfilling candidate data requests. This includes `/candidates/{id}/gdpr-export` (data portability) and `/candidates/{id}/gdpr-forget` (permanent deletion/erasure).
- **Breach Notification**: Processor shall notify Controller of any confirmed security incident involving candidate personal data within 48 hours of discovery.
- **Audits**: Processor shall make available to Controller all information necessary to demonstrate compliance with GDPR Article 28 obligations.
