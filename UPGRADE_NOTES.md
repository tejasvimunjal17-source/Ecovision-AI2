# EcoVision AI — Upgrade Notes

This build preserves the original EcoVision feature set and upgrades the application architecture rather than replacing the website design.

## Implemented

1. **Public landing/auth flow**
   - Public landing page has no application sidebar.
   - Added prominent **Continue with Google** and **Continue with Email** paths.
   - Existing landing content/features remain.
   - Google uses Streamlit OIDC (`st.login("google")`) when configured.

2. **Prakriti AI Connect**
   - Added a floating bottom-right assistant for authenticated users.
   - The full Prakriti page remains available.
   - English/Hindi language selection is retained.
   - Chat history is persisted in Supabase.

3. **Sidebar**
   - Removed Streamlit's native page navigation from the visible UI.
   - Authenticated users get a custom EcoVision sidebar.
   - Logged-out users do not see the sidebar.
   - Officer navigation is role-aware.

4. **User Dashboard + Admin Panel**
   - User session and admin session are separate.
   - Admin Panel uses its own `admin_users` table and bcrypt passwords.
   - Admin can manage users/officers/complaints/categories and view analytics.
   - User sidebar has an Admin Panel entry; Admin Panel can return to the user app.

5. **Supabase PostgreSQL**
   - Replaced runtime SQLite persistence with Supabase PostgreSQL.
   - Tables include users, complaints, complaint timeline, rewards, chat history, recycling centres, carbon records, login attempts, audit logs, categories and admin users.
   - Complaint media is stored in Supabase Storage, with the storage path recorded in PostgreSQL.
   - No `.env` file or local database is included in the upgraded ZIP.

6. **Original features retained**
   - AI waste classification
   - Complaint reporting/tracking
   - Rewards
   - Recycling guide
   - Carbon calculator
   - Dashboard generator
   - Recycling centre locator
   - Awareness hub
   - Certifications/jobs
   - Reports
   - Officer dashboard
   - Prakriti full-page chatbot

## Required deployment setup

1. Run `database/supabase_schema.sql` in Supabase SQL Editor.
2. Configure Streamlit Secrets using `STREAMLIT_SECRETS.example.toml`.
3. Add OpenRouter credentials.
4. Add Supabase URL + service-role key.
5. Configure Google OIDC under `[auth]` if Google sign-in is required.
6. Configure `ADMIN_EMAIL` + `ADMIN_PASSWORD` to bootstrap the first Admin Panel account.

The service-role key must remain server-side and must never be exposed in client-side JavaScript or committed to GitHub.
