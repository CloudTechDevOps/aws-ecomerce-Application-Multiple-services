# Architecture diagrams (teaching set)

Regenerate any time after code changes:

```bash
python docs/generate_diagrams.py
```

Suggested class order:

| # | Image | Use it to explain |
|---|-------|-------------------|
| 01 | `01-aws-architecture.png` | The 2 EC2 + RDS + SMTP topology, ports, security groups, and why this is one monolith behind one Nginx |
| 02 | `02-frontend-services-map.png` | All 9 "services", their files, their login gate, their cart store, and the API each one calls |
| 03 | `03-signup-otp-flow.png` | `pending_signups` staging table and the 2-request OTP signup |
| 04 | `04-login-otp-flow.png` | Password check + the once-per-calendar-day OTP rule |
| 05 | `05-cart-checkout-flow.png` | Everything `POST /api/orders` writes in a single transaction, plus the async receipt e-mail |
| 06 | `06-api-endpoints.png` | Every route, what it touches, and what the server actually authenticates (nothing) |
| 07 | `07-database-schema.png` | 8 tables, foreign keys, cascade behaviour, runtime `CREATE TABLE` |
| 08 | `08-security-findings.png` | Prioritised fix list with the exact file behind each problem |
| 09 | `09-deployment-order.png` | RDS -> backend -> frontend build order and the 2 mistakes that break the demo |
| 10 | `10-request-cheatsheet.png` | One click traced through all 5 layers, and how to debug backwards from an error |
| 11 | `11-service-communication-map.png` | Single-page fan-in: all 9 pages -> Nginx -> the 6 Flask route groups -> the 7 tables -> SMTP, plus what bypasses the proxy |

Every statement in these images was read from `backend/app.py`, `backend/test.sql`,
`frontend/main/google-store.conf` and the `frontend/*` pages - not from the README.
