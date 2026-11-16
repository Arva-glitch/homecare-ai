# API Reference

Base URL: `http://localhost:8000`. Interactive docs: **Swagger UI** at `/docs`, ReDoc at `/redoc`; machine-readable spec in [`openapi.json`](openapi.json).

Authentication: `Authorization: Bearer <access_token>` from `/api/auth/login`. In Swagger, click **Authorize** and log in with `demo@homecare.ai` / `Demo@1234`.

Errors use `{"detail": "message"}` with status codes 400 (business rule), 401 (not authenticated), 404 (not found or not yours), 409 (duplicate), 422 (validation).

## Authentication

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/api/auth/register` | Register | No |
| POST | `/api/auth/login` | Login | No |
| POST | `/api/auth/token` | OAuth2 password flow (used by the Swagger 'Authorize' button) | No |
| POST | `/api/auth/logout` | Logout | Yes |
| GET | `/api/auth/me` | Me | Yes |
| POST | `/api/auth/forgot-password` | Forgot Password | No |
| POST | `/api/auth/reset-password` | Reset Password | No |

## Profile

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/users/me` | Get Profile | Yes |
| PUT | `/api/users/me` | Update Profile | Yes |
| POST | `/api/users/me/change-password` | Change Password | Yes |

## Dashboard

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/dashboard/summary` | Summary | Yes |

## Appliances

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/appliances` | List Appliances | Yes |
| POST | `/api/appliances` | Create Appliance | Yes |
| GET | `/api/appliances/{appliance_id}` | Get Appliance | Yes |
| PUT | `/api/appliances/{appliance_id}` | Update Appliance | Yes |
| DELETE | `/api/appliances/{appliance_id}` | Delete Appliance | Yes |
| POST | `/api/appliances/{appliance_id}/image` | Upload Image | Yes |
| DELETE | `/api/appliances/{appliance_id}/image` | Remove Image | Yes |
| GET | `/api/appliances/{appliance_id}/records` | List Records | Yes |
| POST | `/api/appliances/{appliance_id}/records` | Add Record | Yes |
| DELETE | `/api/appliances/{appliance_id}/records/{record_id}` | Delete Record | Yes |

## Predictive Maintenance

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/predictions/model-info` | Model Info | Yes |
| POST | `/api/predictions/run` | Run All | Yes |
| POST | `/api/predictions/appliances/{appliance_id}` | Run One | Yes |
| GET | `/api/predictions/latest` | Latest | Yes |
| GET | `/api/predictions/history` | History | Yes |

## Maintenance Scheduler

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/schedules` | List Schedules | Yes |
| POST | `/api/schedules` | Create Schedule | Yes |
| GET | `/api/schedules/suggestions` | Suggestions | Yes |
| POST | `/api/schedules/suggestions/accept` | Accept Suggestion | Yes |
| GET | `/api/schedules/{schedule_id}` | Get Schedule | Yes |
| PUT | `/api/schedules/{schedule_id}` | Update Schedule | Yes |
| DELETE | `/api/schedules/{schedule_id}` | Delete Schedule | Yes |
| PATCH | `/api/schedules/{schedule_id}/status` | Update Status | Yes |
| POST | `/api/schedules/{schedule_id}/cancel` | Cancel Schedule | Yes |

## Issue Reporting

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/issues` | List Issues | Yes |
| POST | `/api/issues` | Report Issue | Yes |
| GET | `/api/issues/{issue_id}` | Get Issue | Yes |
| PUT | `/api/issues/{issue_id}` | Update Issue | Yes |
| DELETE | `/api/issues/{issue_id}` | Delete Issue | Yes |
| POST | `/api/issues/{issue_id}/image` | Upload Issue Image | Yes |

## Expenses

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/expenses` | List Expenses | Yes |
| POST | `/api/expenses` | Create Expense | Yes |
| GET | `/api/expenses/summary` | Summary | Yes |
| GET | `/api/expenses/{expense_id}` | Get Expense | Yes |
| PUT | `/api/expenses/{expense_id}` | Update Expense | Yes |
| DELETE | `/api/expenses/{expense_id}` | Delete Expense | Yes |

## Notifications

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/notifications` | List Notifications | Yes |
| GET | `/api/notifications/unread-count` | Unread Count | Yes |
| POST | `/api/notifications/refresh` | Refresh | Yes |
| PATCH | `/api/notifications/{notification_id}/read` | Mark Read | Yes |
| POST | `/api/notifications/read-all` | Mark All Read | Yes |
| DELETE | `/api/notifications/{notification_id}` | Delete Notification | Yes |

## AI HomeCare Assistant

| Method | Path | Description | Auth |
|---|---|---|---|
| POST | `/api/chat` | Send Message | Yes |
| GET | `/api/chat/status` | Chat Status | Yes |
| GET | `/api/chat/sessions` | Sessions | Yes |
| GET | `/api/chat/history` | History | Yes |
| DELETE | `/api/chat/sessions/{session_id}` | Delete Session | Yes |

## Reference data

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/meta/options` | Options | No |

## System

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/api/health` | Health | No |

## Example

```bash
TOKEN=$(curl -s -X POST localhost:8000/api/auth/login -H 'Content-Type: application/json' \
 -d '{"email":"demo@homecare.ai","password":"Demo@1234"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s localhost:8000/api/predictions/latest -H "Authorization: Bearer $TOKEN"
curl -s -X POST localhost:8000/api/chat -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
 -d '{"message":"Which appliance requires immediate maintenance?"}'
```