# Privacy Policy

**Effective Date:** June 9, 2026

At HireIQ ("we," "our," "us"), we are committed to protecting the privacy of recruiters, hiring managers, and candidates whose resumes are processed on our Applicant Tracking System (ATS). This Privacy Policy explains how we collect, use, encrypt, store, and delete personal data in compliance with the General Data Protection Regulation (GDPR) and California Consumer Privacy Act (CCPA).

---

## 1. Information We Collect

We process information uploaded by our B2B customers (companies/recruiters) about job candidates. This includes:
- **Candidate PII**: Full name, email address, physical location, and contact information extracted from uploaded CVs.
- **Professional Details**: Employment history, education details, skill sets, and social profile links (GitHub, LinkedIn).
- **Recruiter Account Info**: Email addresses, passwords, IP addresses, payment logs, and activity logs.

---

## 2. PII Field Encryption (Candidate Safety)
To ensure candidate data remains confidential and secure:
- **Encryption-at-Rest**: Candidate names and emails are automatically encrypted symmetrically at rest in our databases using cryptographically secure **Fernet (AES-128)** encryption.
- Only authorized users belonging to the active organization tenant can request decryption of these candidate records.

---

## 3. How We Process Candidate Data
- **AI Matching & Profiling**: Candidate resumes are parsed dynamically to extract structured job matching metrics and insights.
- **Anonymized Bias Audit**: In "Blind Review" mode, candidate names, gender indications, and specific locations are redacted to calculate unbiased matching scores.
- **LLM Decoupling**: All parsing integrations using external LLM services (e.g. Google Gemini) are performed anonymously without passing raw candidate identifiers, in compliance with GDPR sub-processing limits.

---

## 4. GDPR "Right to be Forgotten" & Portability
Candidates have the right to inspect or request deletion of their data:
- **GDPR Export**: Recruiters can retrieve a candidate's complete structured data package (decrypted name/email, parsed experience, and scores) by calling the `/candidates/{id}/gdpr-export` API.
- **GDPR Forget**: Candidates or recruiters can permanently purge candidate records from our database by requesting deletion via the `/candidates/{id}/gdpr-forget` API. This permanently erases all database records and logs a GDPR-forget compliance audit trail.

---

## 5. Data Retention
We retain candidate records only for as long as needed to fulfill the recruitment workflows of our customers. When an organization cancels its subscription, all tenant candidate profiles and jobs are permanently deleted from database volumes within 30 days.

---

## 6. Contact Us
For data access requests or compliance questions, please contact:
**HireIQ DPO Office**  
Email: [dpo@hireiq.app](mailto:dpo@hireiq.app)
