# HireIQ Backup & Restore Procedures

To protect candidate PII, recruiter configuration, and historical pipeline data, HireIQ relies on automated database-backed backups.

---

## 💾 Backup Coverage & Mechanism

1. **Database Storage**:
   All core platform data is stored in the Supabase PostgreSQL database. This includes:
   - Recruiter accounts, organizations, and subscription plans.
   - Job listings, descriptions, and required skill matrices.
   - Candidates, pipeline stages, interview questions, and notes.
   - **Uploaded Resume Files**: Rebuilt PDF/DOCX files are base64-encoded and stored inside the JSONB `insights` column (`insights.resume_base64`) of the `candidates` table.

   > [!NOTE]
   > Because there is no external file storage dependency (like AWS S3 or persistent local volumes) for resumes, backing up the Supabase database covers **100%** of HireIQ's data.

2. **Backup Types**:
   - **Daily Backups**: Supabase automatically takes daily physical backups of the database.
   - **Point-in-Time Recovery (PITR)**: Enables recovery to any specific second within the retention window.

3. **Retention Policy**:
   - **Free Tier**: Daily backups are retained for up to 7 days. PITR is not available.
   - **Pro Tier (Recommended for production launch)**: Daily backups and PITR are retained for 7 days (can be upgraded to 30 days).

---

## 🔄 How to Perform a Restore

In the event of database corruption, data loss, or a severe application failure, follow these steps to restore the database:

### Option A: Restore to the Active Project (In-Place)
> [!CAUTION]
> Restoring in-place will overwrite all active data. Only do this during an emergency outage window with developer coordination.

1. Log in to the [Supabase Dashboard](https://supabase.com/dashboard).
2. Select the **HireIQ** project.
3. In the left sidebar, navigate to **Database** ➔ **Backups**.
4. Scroll to **Point-in-Time Recovery (PITR)** or **Daily Backups**.
5. Select the backup or specify the exact timestamp (down to the second) you wish to restore to.
6. Click **Restore Database**.

### Option B: Clone to a New Project (Recommended for Validation)
To verify a backup or perform a test restore without affecting the live platform:

1. In the **Database ➔ Backups** section of the active project, click **Clone to New Project** next to the desired backup or PITR timestamp.
2. Select your organization and enter a name for the new temporary project (e.g., `hireiq-restore-test`).
3. Once the clone completes (typically 5-15 minutes), retrieve the `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` of the new project.
4. Point a staging instance of the FastAPI backend to the new project env to verify candidate profile loading and resume decryption.

---

## 👥 Roles & Responsibilities

- **Monitoring**: The engineering lead/DevOps engineer is responsible for checking the Supabase dashboard monthly to ensure daily backups are completing successfully.
- **Drills**: A test restore (using Option B) must be performed once every quarter to guarantee that backup archives are valid and that recovery time objectives (RTO) are met.
