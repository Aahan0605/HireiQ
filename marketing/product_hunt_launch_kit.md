# Product Hunt Launch Kit

## 1. Launch Details
- **Product Name**: HireIQ
- **Tagline**: Hardened Multi-Tenant AI ATS with Blind Bias Audits
- **Primary Category**: Recruitment, Artificial Intelligence, SaaS
- **Secondary Category**: Developer Tools, Analytics

---

## 2. Product Copy

### Short Description (Max 60 chars)
AI-powered ATS with multi-tenancy, blind reviews, and Stripe.

### Description (Max 260 chars)
HireIQ is a hardened B2B SaaS Applicant Tracking System. Upload resumes, parse PII securely (encrypted at rest), and run automated blind reviews to audit bias. Includes billing, queue workers, and role-based access control.

### Long Description (Max 1000 chars)
Finding the right talent is hard. Finding them without bias is even harder. 

Meet HireIQ—an enterprise-grade Applicant Tracking System built for modern recruitment teams. 
We took a high-performance parsing engine and hardened it into a multi-tenant B2B SaaS.

Core Features:
- **Tenant Isolation**: Secure workspace sandboxes for organizations.
- **Granular RBAC**: Owner, Admin, Recruiter, Hiring Manager, and Viewer permissions.
- **ATS Resume Intelligence**: Automatic career tier classification, key strengths, development gaps, and concerns detection.
- **Blind Review Mode**: Anonymizes names, emails, and locations to compute unbiased matching scores.
- **Celery/Redis Workers**: Asynchronous parsing that never blocks API threads.
- **PII Encryption**: Candidate names and emails are encrypted at rest using Fernet (AES-128).
- **GDPR Ready**: Portability export and right-to-be-forgotten deletion endpoints built-in.

We are excited to hear your feedback! Sign up for free today and get 5 resume parses on us.

---

## 3. First Comment (Maker Launch Post)
> Hey Product Hunt! 🐱
>
> I'm the maker behind HireIQ. We built HireIQ because standard hiring workflows are either slow, biased, or insecure. We wanted to create a platform that recruiters can trust with candidate data.
>
> To do this, we focused on **security and privacy first**—candidate names and emails are encrypted in the database, and we built an automated blind review algorithm that strips demographic indicators to audit matching bias. 
> 
> The platform is fully equipped with B2B SaaS multi-tenancy, RBAC, payment tiers, and background workers so it is ready to scale to thousands of resumes daily.
>
> We'd love to hear your feedback. Let us know what features you want to see next!
>
> — The HireIQ Team
