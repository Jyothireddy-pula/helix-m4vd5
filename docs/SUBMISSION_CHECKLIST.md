# Submission Checklist

## Microsoft Forms Fields

Fill these before submitting:

| Field | Value | Verified |
|---|---|---|
| Name | [Your full name] | [ ] |
| Phone number | [Your phone] | [ ] |
| LinkedIn URL | [Your LinkedIn profile URL] | [ ] |
| Resume Google Drive link | [Public, no-login-required link] | [ ] |
| Unlisted YouTube demo URL | [YouTube video URL] | [ ] |
| Public application URL | [Deployed frontend URL] | [ ] |
| Public GitHub repository URL | [GitHub repo URL] | [ ] |
| Email address | jyothireddy@oronzo.io | [ ] |

---

## Pre-Submission Verification

### Application
- [ ] Data ingested: FUELHH actuals for Jan 2026 are in the database
- [ ] Data ingested: WINDFOR forecast vintages for Jan 2026 are in the database
- [ ] Dashboard loads and shows real data (not empty state)
- [ ] Vintage explorer shows forecast vintages for at least one interval
- [ ] Data table shows rows with correct data
- [ ] CSV export works and downloads
- [ ] Cutoff selector changes results
- [ ] Data quality page shows ingestion history

### Tests
- [ ] `cd backend && pytest` passes (all unit tests)
- [ ] `cd frontend && npm run build` succeeds (no build errors)

### Docker
- [ ] `docker-compose up --build` completes without errors
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend accessible at http://localhost:8000/docs

### GitHub Repository
- [ ] Repository is public
- [ ] No .env files, API keys, or credentials committed
- [ ] No personal identifiers in code comments
- [ ] README.md is complete
- [ ] All source code committed and pushed
- [ ] Verify URL in incognito window: repo is publicly accessible

### Video
- [ ] Part 1 (customer presentation) is under 5 minutes
- [ ] Part 2 (technical review) is under 5 minutes
- [ ] Total video is under 10 minutes
- [ ] Video uploaded to YouTube as **Unlisted** (not Private)
- [ ] Verify URL in incognito window: video is watchable without login

### Resume / LinkedIn
- [ ] Google Drive resume is shared as "Anyone with the link can view" (not requires permission request)
- [ ] Verify in incognito: resume opens without requesting access
- [ ] LinkedIn URL is correct and profile is accessible

### Public Application
- [ ] Backend deployed and healthy (GET /api/v1/health returns {"status": "ok"})
- [ ] Frontend deployed and accessible
- [ ] Ingestion run on production database
- [ ] Verify in incognito: app loads with data

---

## Links (fill when ready)

- GitHub: 
- Application: 
- Demo video: 
- Resume: 
- LinkedIn: 

---

## Notes

- The submission form is at [Microsoft Forms link provided by challenge]
- Do not submit until all incognito verifications pass
- The video must be Unlisted, not Private (Private is not viewable by reviewers)
