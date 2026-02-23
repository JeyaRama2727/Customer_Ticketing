# JeyaRamaDesk — Complete Project Documentation

> **Customer Ticketing & Help Desk System**
> Built with Django 5, Django REST Framework, Channels (WebSocket), Celery, and Tailwind CSS.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Accounts App](#2-accounts-app)
3. [Tickets App](#3-tickets-app)
4. [Dashboard App](#4-dashboard-app)
5. [Notifications App](#5-notifications-app)
6. [SLA App](#6-sla-app)
7. [Automation App](#7-automation-app)
8. [Knowledge Base App](#8-knowledge-base-app)
9. [Reports App](#9-reports-app)
10. [Live Chat App](#10-live-chat-app)
11. [Project Configuration](#11-project-configuration-jeyaramadesk)
12. [URL Map](#12-complete-url-map)
13. [Celery Tasks](#13-celery-tasks)
14. [WebSocket Channels](#14-websocket-channels)

---

## 1. Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser    │────▶│  Django/     │────▶│  SQLite/     │
│  (Tailwind)  │◀────│  Daphne      │◀────│  MySQL       │
└──────┬───────┘     └──────┬───────┘     └──────────────┘
       │ WebSocket          │
       └───────────────────▶│──────▶ Redis ──────▶ Celery Worker
                            │                      (SLA checks,
                            │                       Automation)
```

**Tech Stack:**
- **Backend:** Django 5, Django REST Framework, Django Channels (ASGI)
- **Auth:** Session + JWT + Google OAuth (django-allauth)
- **Real-time:** WebSocket via Channels (notifications + live chat)
- **Task Queue:** Celery + Redis (SLA breach checks, automation rules)
- **Database:** SQLite (dev) / MySQL (production)
- **Frontend:** Django templates + Tailwind CSS + Alpine.js

**User Roles:**
| Role | Access Level |
|------|-------------|
| `superadmin` | Full access, user management, system settings |
| `manager` | Manage tickets, agents, SLA, automation, reports |
| `agent` | Handle assigned tickets, respond to customers |
| `customer` | Create tickets, view own tickets, live chat |

---

## 2. Accounts App

Handles user authentication, registration, profile management, and role-based access control.

### Models

#### `User` (table: `jrd_users`)
Custom user model using email as the unique identifier.

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key, auto-generated |
| `email` | EmailField | Unique login identifier |
| `first_name` | CharField(150) | First name |
| `last_name` | CharField(150) | Last name |
| `phone` | CharField(20) | Phone number (optional) |
| `address` | TextField | Address (optional) |
| `avatar` | ImageField | Profile picture (upload to `avatars/%Y/%m/`) |
| `role` | CharField(20) | One of: `superadmin`, `manager`, `agent`, `customer` |
| `department` | CharField(100) | Department (optional) |
| `job_title` | CharField(100) | Job title (optional) |
| `is_active` | BooleanField | Account active status |
| `is_staff` | BooleanField | Django admin access |
| `is_online` | BooleanField | Online status tracking |
| `is_profile_completed` | BooleanField | Profile completion flag (for OAuth users) |
| `timezone_pref` | CharField(50) | User's timezone preference |
| `email_notifications` | BooleanField | Email notification preference |
| `dark_mode` | BooleanField | UI dark mode preference |
| `date_joined` | DateTimeField | Registration timestamp |
| `last_login` | DateTimeField | Last login timestamp |
| `updated_at` | DateTimeField | Last update timestamp |

**Properties:**
| Property | Returns |
|----------|---------|
| `full_name` | `"First Last"` |
| `initials` | `"FL"` (first letters) |
| `is_superadmin` | `True` if role is superadmin |
| `is_manager` | `True` if role is manager |
| `is_agent` | `True` if role is agent |
| `is_customer` | `True` if role is customer |
| `is_staff_member` | `True` for superadmin/manager/agent |

#### `UserManager`
| Method | Description |
|--------|-------------|
| `create_user(email, password, **fields)` | Create a regular user (defaults to customer role) |
| `create_superuser(email, password, **fields)` | Create a superuser with superadmin role |

#### `LoginAuditLog` (table: `jrd_login_audit`)
Tracks all login attempts for security auditing.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `user` | FK → User | The user (nullable if failed login) |
| `email_attempted` | EmailField | Email used in the attempt |
| `status` | CharField(10) | `success`, `failed`, or `locked` |
| `ip_address` | GenericIPAddressField | Client IP address |
| `user_agent` | TextField | Browser user agent string |
| `timestamp` | DateTimeField | When the attempt occurred |

---

### Views (Template-based)

| Function | URL | Method | Description |
|----------|-----|--------|-------------|
| `login_view` | `/accounts/login/` | GET/POST | Login page; redirects to dashboard on success |
| `logout_view` | `/accounts/logout/` | POST | Logout; clears online status |
| `register_view` | `/accounts/register/` | GET/POST | Customer self-registration with validation |
| `profile_view` | `/accounts/profile/` | GET/POST | View/update profile including avatar upload |
| `change_password_view` | `/accounts/change-password/` | GET/POST | Change password with current password verification |
| `complete_profile_view` | `/accounts/complete-profile/` | GET/POST | Force Google OAuth users to complete their profile |
| `user_list_view` | `/accounts/users/` | GET | List all users with filters (staff only) |
| `user_create_view` | `/accounts/users/create/` | GET/POST | Create a new user (manager+ only) |
| `user_edit_view` | `/accounts/users/<uuid>/edit/` | GET/POST | Edit user; role changes restricted to superadmin |
| `user_toggle_active_view` | `/accounts/users/<uuid>/toggle/` | POST | Activate/deactivate user (manager+ only) |
| `audit_log_view` | `/accounts/audit-logs/` | GET | View login audit logs (superadmin only) |

---

### Services

#### `AuthService`
| Method | Description |
|--------|-------------|
| `login_user(request, email, password)` | Authenticate user, create session, log audit entry. Returns `(user, error)` |
| `logout_user(request)` | End session and set `is_online=False` |

#### `UserService`
| Method | Description |
|--------|-------------|
| `create_user(data)` | Create a new user with atomic transaction |
| `update_user(user, data)` | Update user profile fields |
| `get_agents()` | Get all active agents/managers/superadmins |
| `get_customers()` | Get all active customers |
| `get_user_stats()` | Return aggregate user count statistics |

---

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/accounts/users/` | GET | List users (filterable by `role`, `is_active`) |
| `/api/accounts/users/` | POST | Create user (manager+ only) |
| `/api/accounts/users/<id>/` | GET/PUT/PATCH/DELETE | User CRUD |
| `/api/accounts/users/me/` | GET | Get current authenticated user profile |
| `/api/accounts/users/agents/` | GET | List all active agents |
| `/api/accounts/token/` | POST | Obtain JWT access + refresh token |
| `/api/accounts/token/refresh/` | POST | Refresh JWT access token |

---

### Permissions

| Class | Who can access |
|-------|---------------|
| `IsSuperAdmin` | Superadmin only |
| `IsManager` | Superadmin or Manager |
| `IsAgent` | Superadmin, Manager, or Agent |
| `IsStaffMember` | Any internal staff (not customer) |
| `IsCustomer` | Customer only |
| `IsOwnerOrStaff` | Object owner or any staff member |

---

### OAuth Adapters

#### `AccountAdapter`
- Ensures all signups default to `customer` role
- Sets login redirect URL

#### `SocialAccountAdapter`
- Connects Google account to existing user with same email
- Populates profile fields from Google data
- Assigns `customer` role to new social signups

---

## 3. Tickets App

Core ticketing system with full lifecycle tracking, comments, attachments, and audit trail.

### Models

#### `Category` (table: `jrd_categories`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `name` | CharField(100) | Category name (unique) |
| `slug` | SlugField(120) | URL-safe slug (auto-generated) |
| `description` | TextField | Description |
| `color` | CharField(7) | Hex color code (default `#6366f1`) |
| `is_active` | BooleanField | Active/inactive status |
| `created_at` | DateTimeField | Creation timestamp |

#### `Tag` (table: `jrd_tags`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `name` | CharField(50) | Tag name (unique) |
| `slug` | SlugField(60) | URL-safe slug |
| `color` | CharField(7) | Hex color code |

#### `Ticket` (table: `jrd_tickets`)
The heart of the system — designed for millions of records with comprehensive indexing.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `ticket_id` | CharField(20) | Human-readable ID like `JRD-A3X9K2` (unique, auto-generated) |
| `title` | CharField(300) | Ticket subject |
| `description` | TextField | Rich text description |
| `category` | FK → Category | Ticket category (optional) |
| `priority` | CharField(10) | `low`, `medium`, `high`, `urgent` |
| `status` | CharField(15) | `open`, `in_progress`, `pending`, `resolved`, `closed` |
| `tags` | M2M → Tag | Tags for classification |
| `customer` | FK → User | Customer who created the ticket |
| `assigned_agent` | FK → User | Agent handling the ticket (optional) |
| `sla_policy` | FK → SLAPolicy | Applied SLA policy (optional) |
| `sla_response_deadline` | DateTimeField | Deadline for first response |
| `sla_resolution_deadline` | DateTimeField | Deadline for resolution |
| `sla_response_met` | BooleanField | Whether response SLA was met |
| `sla_resolution_met` | BooleanField | Whether resolution SLA was met |
| `first_response_at` | DateTimeField | When first staff response occurred |
| `resolved_at` | DateTimeField | When ticket was resolved |
| `due_date` | DateTimeField | Manual due date (optional) |
| `source` | CharField(20) | `web`, `email`, `api`, `phone` |
| `is_escalated` | BooleanField | Whether ticket is escalated |
| `escalation_level` | SmallInt | Escalation level (0–3) |
| `csat_rating` | SmallInt | Customer satisfaction rating (1–5) |
| `csat_feedback` | TextField | Customer feedback text |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last update timestamp |

**Properties:**
| Property | Description |
|----------|-------------|
| `is_overdue` | `True` if past due_date and not resolved/closed |
| `sla_response_breached` | `True` if past response deadline with no first response |
| `sla_resolution_breached` | `True` if past resolution deadline and not resolved/closed |
| `priority_color` | Hex color for priority badge |
| `status_color` | Hex color for status badge |

#### `TicketComment` (table: `jrd_ticket_comments`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `ticket` | FK → Ticket | Parent ticket |
| `author` | FK → User | Comment author |
| `content` | TextField | Comment body |
| `comment_type` | CharField(15) | `reply` (visible to all), `internal_note` (staff only), `system` |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last edit timestamp |

#### `TicketAttachment` (table: `jrd_ticket_attachments`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `ticket` | FK → Ticket | Parent ticket |
| `comment` | FK → TicketComment | Associated comment (optional) |
| `file` | FileField | Uploaded file (to `attachments/%Y/%m/%d/`) |
| `filename` | CharField(255) | Original filename |
| `file_size` | PositiveIntegerField | Size in bytes |
| `content_type` | CharField(100) | MIME type |
| `uploaded_by` | FK → User | Uploader |
| `uploaded_at` | DateTimeField | Upload timestamp |

#### `TicketActivity` (table: `jrd_ticket_activities`)
Complete audit trail of all ticket changes.

| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `ticket` | FK → Ticket | Parent ticket |
| `activity_type` | CharField(20) | 15 types: `created`, `status_changed`, `assigned`, `escalated`, `priority_changed`, `commented`, `tag_added`, `category_changed`, `resolved`, `closed`, `reopened`, `due_date_set`, `sla_breached`, `attachment_added`, `updated` |
| `actor` | FK → User | Who performed the action |
| `old_value` | CharField(255) | Previous value |
| `new_value` | CharField(255) | New value |
| `description` | TextField | Human-readable description |
| `created_at` | DateTimeField | When it happened |

---

### Views (Template-based)

| Function | URL | Method | Description |
|----------|-----|--------|-------------|
| `ticket_list_view` | `/tickets/` | GET | List tickets with role-based filtering, search, pagination (25/page) |
| `ticket_create_view` | `/tickets/create/` | GET/POST | Create a new ticket with optional file attachments |
| `ticket_detail_view` | `/tickets/<ticket_id>/` | GET | Full ticket detail: comments, activities, attachments. Customers can't see internal notes |
| `ticket_update_view` | `/tickets/<ticket_id>/update/` | POST | Update ticket properties (status, priority, assignment, category) |
| `ticket_comment_view` | `/tickets/<ticket_id>/comment/` | POST | Add a comment; customers restricted to `reply` type only |
| `ticket_assign_view` | `/tickets/<ticket_id>/assign/` | POST | Quick-assign to self or another agent (staff only) |

---

### Services

#### `TicketService`
| Method | Description |
|--------|-------------|
| `create_ticket(data, customer, files)` | Create ticket, record activity, process attachments, apply SLA policy, run automation rules |
| `update_ticket(ticket, data, actor)` | Update fields and track every change as an activity record |
| `add_comment(ticket, author, content, comment_type, files)` | Add comment, track first response for SLA compliance, create activity |
| `assign_ticket(ticket, agent, actor)` | Assign/reassign ticket, log activity |
| `escalate_ticket(ticket, actor, reason)` | Escalate ticket, increment level, log activity |
| `_process_attachments(ticket, comment, files, uploader)` | Save file attachments to database |
| `_apply_sla(ticket)` | Find matching SLA policy by priority, set response/resolution deadlines |
| `get_ticket_stats(user)` | Get ticket counts grouped by status (role-aware) |

---

### Signals

| Signal | Trigger | What it does |
|--------|---------|--------------|
| `ticket_pre_save` | Before Ticket save | Caches old field values to detect changes |
| `ticket_post_save` | After Ticket save | Sends notifications for: new ticket, assignment change, status change, priority change |
| `comment_post_save` | After TicketComment save | Sends notification for new non-system comments |

---

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/tickets/tickets/` | GET | List tickets (role-based filtering) |
| `/api/tickets/tickets/` | POST | Create ticket |
| `/api/tickets/tickets/<id>/` | GET/PUT/PATCH/DELETE | Ticket CRUD |
| `/api/tickets/tickets/<id>/comment/` | POST | Add comment |
| `/api/tickets/tickets/<id>/comments/` | GET | List comments |
| `/api/tickets/tickets/<id>/assign/` | POST | Assign to agent |
| `/api/tickets/tickets/<id>/escalate/` | POST | Escalate ticket |
| `/api/tickets/tickets/stats/` | GET | Get ticket statistics |
| `/api/tickets/categories/` | GET/POST | Category CRUD |
| `/api/tickets/tags/` | GET/POST | Tag CRUD |

---

## 4. Dashboard App

Main landing page with role-based analytics and metrics.

### Views

| Function | URL | Description |
|----------|-----|-------------|
| `dashboard_index_view` | `/` (root) | Main dashboard with: ticket stats, 7-day trend chart data, priority/status distribution, recent tickets, agent performance (staff), SLA stats (staff), customer stats |

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/stats/` | GET | JSON ticket counts, new this week, SLA breaches (staff only) |

---

## 5. Notifications App

In-app notification system with real-time WebSocket push.

### Models

#### `Notification`
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `user` | FK → User | Recipient |
| `title` | CharField(255) | Notification headline |
| `message` | TextField | Notification body |
| `notification_type` | CharField(25) | One of 10 types (see below) |
| `ticket` | FK → Ticket | Related ticket (optional) |
| `is_read` | BooleanField | Read/unread status |
| `read_at` | DateTimeField | When it was read |
| `created_at` | DateTimeField | Creation timestamp |

**Notification Types:** `ticket_created`, `ticket_assigned`, `ticket_updated`, `ticket_resolved`, `comment_added`, `status_change`, `priority_change`, `sla_breach`, `automation`, `system`

| Method | Description |
|--------|-------------|
| `mark_read()` | Set `is_read=True` and record `read_at` timestamp |

---

### Views

| Function | URL | Method | Description |
|----------|-----|--------|-------------|
| `notification_list` | `/notifications/` | GET | Display notifications with read/unread filter (100 max) |
| `notification_open` | `/notifications/<uuid>/open/` | GET | Mark as read and redirect to linked ticket |
| `mark_read` | `/notifications/<uuid>/read/` | POST | Mark single notification as read (AJAX or redirect) |
| `mark_all_read` | `/notifications/mark-all-read/` | POST | Mark all unread as read (AJAX or redirect) |
| `unread_count_api` | `/notifications/unread-count/` | GET | JSON endpoint for topbar badge count |

---

### Services

#### `NotificationService`
| Method | Description |
|--------|-------------|
| `create_notification(user, title, message, type, ticket)` | Create notification + push via WebSocket |
| `get_unread_count(user)` | Return unread count |
| `get_recent(user, limit)` | Return most recent notifications |
| `notify_new_ticket(ticket)` | Notify managers/superadmins about new ticket |
| `notify_new_comment(comment)` | Notify ticket owner, assigned agent; if customer commented, also notify admins/managers |
| `notify_ticket_assigned(ticket)` | Notify the assigned agent |
| `notify_sla_breach(ticket, breach_type)` | Notify assigned agent + all managers about SLA breach |
| `notify_status_change(ticket, old_status)` | Notify customer and agent on status change |
| `notify_priority_change(ticket, old_priority)` | Notify customer and agent on priority change |
| `_push_realtime(notification)` | Push to WebSocket channel group (fails silently if unavailable) |

---

### WebSocket Consumer

#### `NotificationConsumer`
- **Connect:** Joins `notifications_{user_id}` channel group
- **Disconnect:** Leaves group
- **send_notification:** Forwards notification JSON to the client
- One-way push only (server → client)

**WebSocket URL:** `ws://host/desk/ws/notifications/`

---

### Context Processor

`unread_notifications_count(request)` — Injects `unread_notifications_count` into every template for the topbar badge.

---

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notifications/` | GET | List user's notifications (filterable by `is_read`) |
| `/api/notifications/<id>/read/` | POST | Mark single as read |
| `/api/notifications/mark_all_read/` | POST | Mark all as read |

---

## 6. SLA App

Service Level Agreement policies with automatic breach detection and notifications.

### Models

#### `SLAPolicy` (table: `jrd_sla_policies`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `name` | CharField(100) | Policy name (e.g., "Urgent SLA") |
| `description` | TextField | Description |
| `priority` | CharField(10) | `low`, `medium`, `high`, `urgent` |
| `response_time_hours` | PositiveIntegerField | Max hours for first response |
| `resolution_time_hours` | PositiveIntegerField | Max hours for resolution |
| `escalation_time_hours` | PositiveIntegerField | Hours before auto-escalation (0 = disabled) |
| `is_active` | BooleanField | Active/inactive |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last update timestamp |

#### `SLABreach` (table: `jrd_sla_breaches`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `ticket` | FK → Ticket | The breached ticket |
| `policy` | FK → SLAPolicy | The policy that was breached |
| `breach_type` | CharField(10) | `response` or `resolution` |
| `deadline` | DateTimeField | The SLA deadline that was missed |
| `breached_at` | DateTimeField | When the breach was detected |
| `notified` | BooleanField | Whether notifications were sent |

---

### How SLA Works (End-to-End Flow)

1. **Ticket created** → `TicketService._apply_sla()` finds matching policy by priority → stamps `sla_response_deadline` and `sla_resolution_deadline` on the ticket
2. **Agent responds** → `first_response_at` is recorded, `sla_response_met` is set `True`/`False`
3. **Ticket resolved** → `sla_resolution_met` is evaluated
4. **Every 5 minutes** → Celery task `check_sla_breaches` scans open tickets for missed deadlines
5. **Breach found** → `SLABreach` record created + notification sent to agent + managers

---

### Views

| Function | URL | Method | Description |
|----------|-----|--------|-------------|
| `sla_list_view` | `/sla/` | GET | List policies, stats, recent breaches (staff only) |
| `sla_create_view` | `/sla/create/` | GET/POST | Create new SLA policy (manager+ only) |
| `sla_edit_view` | `/sla/<id>/edit/` | GET/POST | Edit SLA policy (manager+ only) |

---

### Services

#### `SLAService`
| Method | Description |
|--------|-------------|
| `check_all_breaches()` | Scan all open tickets for response/resolution breaches; create breach records + send notifications |
| `get_sla_stats()` | Return compliance stats: total, met/breached counts, percentage rates |

---

### Celery Task

| Task | Schedule | Description |
|------|----------|-------------|
| `check_sla_breaches` | Every 5 minutes (300s) | Calls `SLAService.check_all_breaches()` |

---

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sla/policies/` | GET/POST | SLA Policy CRUD (staff only) |
| `/api/sla/policies/<id>/` | GET/PUT/PATCH/DELETE | Single policy |
| `/api/sla/policies/stats/` | GET | SLA statistics |
| `/api/sla/breaches/` | GET | List breaches (filterable by `breach_type`, `notified`) |

---

## 7. Automation App

Rule-based workflow engine — "if this, then that" for tickets.

### Models

#### `AutomationRule` (table: `jrd_automation_rules`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | CharField(200) | Rule name |
| `description` | TextField | Description |
| `trigger_event` | CharField(30) | When to evaluate (see table below) |
| `conditions` | JSONField | Conditions to match (e.g., `{"priority": "urgent"}`) |
| `action_type` | CharField(30) | What to do (see table below) |
| `action_params` | JSONField | Action parameters (e.g., `{"agent_id": "uuid"}`) |
| `priority_order` | PositiveIntegerField | Execution order (lower = first) |
| `is_active` | BooleanField | Active/inactive |
| `stop_processing` | BooleanField | Stop further rules after this one matches |
| `created_by` | FK → User | Rule creator |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last update timestamp |

**Trigger Events:**
| Value | Description |
|-------|-------------|
| `ticket_created` | A new ticket is submitted |
| `ticket_updated` | Any ticket field changes |
| `ticket_assigned` | A ticket is assigned |
| `ticket_commented` | A comment is added |
| `sla_breach` | An SLA deadline is missed |
| `ticket_idle` | Ticket has no activity for 24+ hours |

**Action Types:**
| Value | Params Example | Description |
|-------|---------------|-------------|
| `assign_agent` | `{"agent_id": "uuid"}` | Auto-assign to a specific agent |
| `change_priority` | `{"priority": "high"}` | Change ticket priority |
| `change_status` | `{"status": "in_progress"}` | Change ticket status |
| `add_tag` | `{"tag": "billing"}` | Add a tag |
| `send_notification` | `{"message": "...", "recipients": "agent"}` | Send custom notification |
| `escalate` | `{}` | Escalate ticket (max level 3) |
| `add_comment` | `{"content": "..."}` | Add an internal note |

#### `AutomationLog` (table: `jrd_automation_logs`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `rule` | FK → AutomationRule | The rule that fired |
| `ticket` | FK → Ticket | The ticket it ran on |
| `status` | CharField(10) | `success`, `failed`, or `skipped` |
| `action_taken` | TextField | Description of action |
| `error_message` | TextField | Error details (if failed) |
| `executed_at` | DateTimeField | Execution timestamp |

---

### How Automation Works

1. A **trigger event** occurs (e.g., ticket created)
2. The system finds all **active rules** for that trigger, ordered by `priority_order`
3. For each rule, **conditions** are evaluated against the ticket's fields
4. If conditions match, the **action** is executed
5. Execution is **logged** in `AutomationLog`
6. If `stop_processing` is `True`, no further rules are evaluated

**Condition matching** supports:
- Direct field comparison: `{"priority": "urgent"}`
- Nested lookups with `__`: `{"category__name": "Billing"}`
- Case-insensitive string comparison

---

### Views

| Function | URL | Method | Description |
|----------|-----|--------|-------------|
| `rule_list_view` | `/automation/` | GET | List all rules with stats and recent logs |
| `rule_create_view` | `/automation/create/` | GET/POST | Create new rule with JSON conditions/params |
| `rule_edit_view` | `/automation/<uuid>/edit/` | GET/POST | Edit existing rule |
| `rule_delete_view` | `/automation/<uuid>/delete/` | POST | Delete rule (superadmin only) |
| `rule_logs_view` | `/automation/logs/` | GET | View execution logs with status filter |

---

### Services

#### `AutomationService`
| Method | Description |
|--------|-------------|
| `run_rules(trigger_event, ticket)` | Evaluate all active rules for a trigger; execute matching ones |
| `_match_conditions(rule, ticket)` | Check if ticket fields match rule's JSON conditions |
| `_execute_action(rule, ticket)` | Dispatch to the appropriate action handler |
| `_action_assign_agent(ticket, params)` | Assign ticket to specified agent |
| `_action_change_priority(ticket, params)` | Change priority with activity logging |
| `_action_change_status(ticket, params)` | Change status with activity logging |
| `_action_add_tag(ticket, params)` | Add tag (create if doesn't exist) |
| `_action_escalate(ticket, params)` | Escalate ticket (increment level, max 3) |
| `_action_add_comment(ticket, params)` | Add internal note |
| `_action_send_notification(ticket, params)` | Send notification to agent or customer |
| `get_rule_stats()` | Return rule/execution statistics |

---

### Celery Task

| Task | Schedule | Description |
|------|----------|-------------|
| `run_idle_ticket_rules` | Every 60 seconds | Find tickets idle for 24+ hours, run `ticket_idle` rules (max 100/run) |

---

## 8. Knowledge Base App

Public-facing help center with articles, categories, search, and feedback.

### Models

#### `KBCategory` (table: `jrd_kb_categories`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | CharField(200) | Category name |
| `slug` | SlugField(200) | URL slug (unique, auto-generated) |
| `description` | TextField | Category description |
| `icon` | CharField(50) | CSS icon class |
| `parent` | FK → self | Parent category (nullable, tree structure) |
| `order` | PositiveIntegerField | Display order |
| `is_active` | BooleanField | Active status |
| `created_at` | DateTimeField | Creation timestamp |

**Property:** `article_count` — Count of published articles in this category.

#### `Article` (table: `jrd_kb_articles`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `title` | CharField(300) | Article title |
| `slug` | SlugField(300) | URL slug (unique, auto-generated) |
| `category` | FK → KBCategory | Article category |
| `body` | TextField | Article content (HTML/Markdown) |
| `excerpt` | TextField(500) | Summary (auto-generated from body if empty) |
| `status` | CharField(15) | `draft`, `published`, `archived` |
| `meta_title` | CharField(200) | SEO title |
| `meta_description` | TextField(300) | SEO description |
| `views_count` | PositiveIntegerField | Total views |
| `helpful_yes` | PositiveIntegerField | Positive feedback count |
| `helpful_no` | PositiveIntegerField | Negative feedback count |
| `is_internal` | BooleanField | Visible to staff only |
| `is_featured` | BooleanField | Featured on homepage |
| `author` | FK → User | Article author |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last update timestamp |
| `published_at` | DateTimeField | Publication timestamp |

**Properties:**
| Property | Description |
|----------|-------------|
| `helpfulness_rate` | Percentage of `helpful_yes` out of total votes |
| `reading_time` | Estimated minutes (word count / 200) |

#### `ArticleAttachment` (table: `jrd_kb_attachments`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | BigAutoField | Primary key |
| `article` | FK → Article | Parent article |
| `file` | FileField | Uploaded file (to `kb_attachments/%Y/%m/`) |
| `filename` | CharField(255) | Original filename |
| `file_size` | PositiveIntegerField | Size in bytes |
| `uploaded_at` | DateTimeField | Upload timestamp |

---

### Views

| Function | URL | Method | Description |
|----------|-----|--------|-------------|
| `kb_home_view` | `/knowledge-base/` | GET | Public homepage: categories, featured articles, popular articles |
| `kb_category_view` | `/knowledge-base/category/<slug>/` | GET | Articles in a category; internal articles hidden from customers |
| `kb_article_view` | `/knowledge-base/article/<slug>/` | GET | View article; auto-increments view count; access control for drafts/internal |
| `kb_article_feedback` | `/knowledge-base/article/<slug>/feedback/` | POST | AJAX helpfulness feedback (yes/no) |
| `kb_search_view` | `/knowledge-base/search/` | GET | Search articles by title, body, excerpt |
| `kb_manage_list_view` | `/knowledge-base/manage/` | GET | Staff: manage all articles with filters |
| `kb_article_create_view` | `/knowledge-base/manage/create/` | GET/POST | Staff: create new article |
| `kb_article_edit_view` | `/knowledge-base/manage/<slug>/edit/` | GET/POST | Staff: edit existing article |

---

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/knowledge-base/categories/` | GET/POST | KB Category CRUD |
| `/api/knowledge-base/articles/` | GET/POST | Article CRUD (public read for published, staff write) |
| `/api/knowledge-base/articles/<id>/` | GET/PUT/PATCH/DELETE | Single article |
| `/api/knowledge-base/articles/search/` | GET | Search articles by `q` parameter |
| `/api/knowledge-base/articles/<id>/feedback/` | POST | Submit helpfulness vote |

---

## 9. Reports App

Reporting and analytics with CSV export support.

### Models

#### `SavedReport` (table: `jrd_saved_reports`)
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `name` | CharField(200) | Report name |
| `report_type` | CharField(30) | `ticket_summary`, `agent_performance`, `sla_compliance`, `category_breakdown`, `customer_satisfaction` |
| `filters` | JSONField | Saved filter parameters |
| `created_by` | FK → User | Report creator |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last update timestamp |

---

### Views

| Function | URL | Method | Description |
|----------|-----|--------|-------------|
| `report_index_view` | `/reports/` | GET | Report selection page (staff only) |
| `ticket_summary_report` | `/reports/ticket-summary/` | GET | Ticket summary with date range, priority/category/source breakdown; **CSV export** |
| `agent_performance_report` | `/reports/agent-performance/` | GET | Agent metrics: assigned, resolved, open counts; **CSV export** |
| `sla_compliance_report` | `/reports/sla-compliance/` | GET | SLA compliance stats, breach details; **CSV export** |

All reports support `?export=csv` to download data as CSV files.

---

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/reports/ticket-summary/` | GET | JSON ticket summary report data (staff only) |

---

## 10. Live Chat App

Real-time chat between customers and agents using WebSocket.

### Models

#### `ChatRoom`
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `customer` | FK → User | Customer who started the chat |
| `agent` | FK → User | Assigned agent (nullable) |
| `ticket` | FK → Ticket | Linked ticket (optional) |
| `subject` | CharField(255) | Chat subject (default "Live Chat") |
| `status` | CharField(10) | `waiting`, `active`, `closed` |
| `created_at` | DateTimeField | Creation timestamp |
| `updated_at` | DateTimeField | Last update timestamp |
| `closed_at` | DateTimeField | When chat was closed |

#### `ChatMessage`
| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Primary key |
| `room` | FK → ChatRoom | Parent chat room |
| `sender` | FK → User | Message sender |
| `content` | TextField | Message text |
| `message_type` | CharField(10) | `text`, `system`, `image` |
| `is_read` | BooleanField | Read status |
| `created_at` | DateTimeField | When message was sent |

---

### Views

| Function | URL | Method | Description |
|----------|-----|--------|-------------|
| `chat_room_list` | `/chat/` | GET | List chat rooms; staff sees own + waiting, customers see own |
| `chat_room` | `/chat/<uuid>/` | GET | Render chat room; auto-assigns agent to waiting rooms; marks messages as read |
| `start_chat` | `/chat/start/` | POST | Customer starts a new chat session |
| `close_chat` | `/chat/<uuid>/close/` | POST | Close a chat room |
| `send_message` | `/chat/<uuid>/send/` | POST | HTTP fallback for sending messages |
| `fetch_messages` | `/chat/<uuid>/messages/` | GET | Poll for messages after a given timestamp |
| `unread_chat_count` | `/chat/unread-count/` | GET | JSON endpoint for unread message count |

---

### WebSocket Consumer

#### `ChatConsumer`
Bidirectional real-time messaging.

| Method | Description |
|--------|-------------|
| `connect()` | Join `chat_{room_id}` group; accept authenticated users |
| `disconnect(close_code)` | Leave room group |
| `receive(text_data)` | Parse incoming message → save to DB → broadcast to room |
| `chat_message(event)` | Forward message to WebSocket client |
| `user_event(event)` | Forward join/leave events |
| `typing_event(event)` | Forward typing indicators (excludes sender) |

**WebSocket URL:** `ws://host/desk/ws/chat/<room_id>/`

**Message types sent to client:**
```json
{"type": "chat_message", "message": "...", "sender_name": "...", "sender_role": "...", "timestamp": "..."}
{"type": "user_event", "event": "joined/left", "user_name": "..."}
{"type": "typing", "user_name": "...", "is_typing": true}
```

---

## 11. Project Configuration (`jeyaramadesk/`)

### Settings Summary

| Setting | Value |
|---------|-------|
| `AUTH_USER_MODEL` | `accounts.User` |
| `ASGI_APPLICATION` | `jeyaramadesk.asgi.application` |
| `TIME_ZONE` | `Asia/Kolkata` |
| `URL_PREFIX` | `/desk` (all routes under `/desk/`) |
| `DATABASE` | SQLite (dev) / MySQL (prod via env vars) |
| `REST_FRAMEWORK` | JWT + Session auth, 25/page, throttle: 30/min anon, 120/min user |
| `SIMPLE_JWT` | 2h access token, 7d refresh, rotate + blacklist |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` |
| `CELERY_BEAT_SCHEDULE` | SLA check every 5min, automation every 1min |
| `FILE_UPLOAD_MAX` | 10 MB |

### Middleware

#### `AuditMiddleware`
Logs all non-GET request metadata (method, path, user, IP, status code) for authenticated users.

#### `RateLimitMiddleware`
In-memory per-IP rate limiter: max 10 requests per 60 seconds on login/token endpoints. Returns HTTP 429 if exceeded.

### Utilities

| Function | Description |
|----------|-------------|
| `custom_exception_handler(exc, context)` | Enhanced DRF exception handler; logs errors, standardizes format |

### Celery App
- App name: `jeyaramadesk`
- Auto-discovers tasks from all installed apps
- `debug_task` for health checks

### ASGI Configuration
`ProtocolTypeRouter` for:
- **HTTP** → Django ASGI app
- **WebSocket** → `AuthMiddlewareStack` routing to notification + livechat consumers

---

## 12. Complete URL Map

All routes are prefixed with `/desk/` in production.

### Template Views
| URL | App | View |
|-----|-----|------|
| `/` | dashboard | `dashboard_index_view` |
| `/accounts/login/` | accounts | `login_view` |
| `/accounts/logout/` | accounts | `logout_view` |
| `/accounts/register/` | accounts | `register_view` |
| `/accounts/profile/` | accounts | `profile_view` |
| `/accounts/complete-profile/` | accounts | `complete_profile_view` |
| `/accounts/change-password/` | accounts | `change_password_view` |
| `/accounts/users/` | accounts | `user_list_view` |
| `/accounts/users/create/` | accounts | `user_create_view` |
| `/accounts/users/<uuid>/edit/` | accounts | `user_edit_view` |
| `/accounts/users/<uuid>/toggle/` | accounts | `user_toggle_active_view` |
| `/accounts/audit-logs/` | accounts | `audit_log_view` |
| `/tickets/` | tickets | `ticket_list_view` |
| `/tickets/create/` | tickets | `ticket_create_view` |
| `/tickets/<ticket_id>/` | tickets | `ticket_detail_view` |
| `/tickets/<ticket_id>/update/` | tickets | `ticket_update_view` |
| `/tickets/<ticket_id>/comment/` | tickets | `ticket_comment_view` |
| `/tickets/<ticket_id>/assign/` | tickets | `ticket_assign_view` |
| `/sla/` | sla | `sla_list_view` |
| `/sla/create/` | sla | `sla_create_view` |
| `/sla/<id>/edit/` | sla | `sla_edit_view` |
| `/automation/` | automation | `rule_list_view` |
| `/automation/create/` | automation | `rule_create_view` |
| `/automation/<uuid>/edit/` | automation | `rule_edit_view` |
| `/automation/<uuid>/delete/` | automation | `rule_delete_view` |
| `/automation/logs/` | automation | `rule_logs_view` |
| `/knowledge-base/` | knowledge_base | `kb_home_view` |
| `/knowledge-base/search/` | knowledge_base | `kb_search_view` |
| `/knowledge-base/category/<slug>/` | knowledge_base | `kb_category_view` |
| `/knowledge-base/article/<slug>/` | knowledge_base | `kb_article_view` |
| `/knowledge-base/article/<slug>/feedback/` | knowledge_base | `kb_article_feedback` |
| `/knowledge-base/manage/` | knowledge_base | `kb_manage_list_view` |
| `/knowledge-base/manage/create/` | knowledge_base | `kb_article_create_view` |
| `/knowledge-base/manage/<slug>/edit/` | knowledge_base | `kb_article_edit_view` |
| `/reports/` | reports | `report_index_view` |
| `/reports/ticket-summary/` | reports | `ticket_summary_report` |
| `/reports/agent-performance/` | reports | `agent_performance_report` |
| `/reports/sla-compliance/` | reports | `sla_compliance_report` |
| `/notifications/` | notifications | `notification_list` |
| `/notifications/<uuid>/open/` | notifications | `notification_open` |
| `/notifications/<uuid>/read/` | notifications | `mark_read` |
| `/notifications/mark-all-read/` | notifications | `mark_all_read` |
| `/notifications/unread-count/` | notifications | `unread_count_api` |
| `/chat/` | livechat | `chat_room_list` |
| `/chat/start/` | livechat | `start_chat` |
| `/chat/<uuid>/` | livechat | `chat_room` |
| `/chat/<uuid>/close/` | livechat | `close_chat` |
| `/chat/<uuid>/send/` | livechat | `send_message` |
| `/chat/<uuid>/messages/` | livechat | `fetch_messages` |
| `/chat/unread-count/` | livechat | `unread_chat_count` |

### REST API Endpoints
| URL | App |
|-----|-----|
| `/api/accounts/users/` | accounts |
| `/api/accounts/token/` | JWT auth |
| `/api/accounts/token/refresh/` | JWT refresh |
| `/api/tickets/tickets/` | tickets |
| `/api/tickets/categories/` | tickets |
| `/api/tickets/tags/` | tickets |
| `/api/sla/policies/` | sla |
| `/api/sla/breaches/` | sla |
| `/api/dashboard/stats/` | dashboard |
| `/api/notifications/` | notifications |
| `/api/reports/ticket-summary/` | reports |
| `/api/knowledge-base/categories/` | knowledge_base |
| `/api/knowledge-base/articles/` | knowledge_base |

---

## 13. Celery Tasks

| Task | App | Schedule | Description |
|------|-----|----------|-------------|
| `sla.tasks.check_sla_breaches` | sla | Every 5 minutes | Scan open tickets for SLA deadline breaches |
| `automation.run_idle_ticket_rules` | automation | Every 60 seconds | Run automation rules on idle tickets (24h+ no activity) |
| `jeyaramadesk.celery.debug_task` | core | Manual | Health check task |

**Required services:**
```bash
# Redis (message broker)
redis-server

# Celery worker
celery -A jeyaramadesk worker -l info

# Celery beat (task scheduler)
celery -A jeyaramadesk beat -l info
```

---

## 14. WebSocket Channels

| URL | Consumer | Purpose |
|-----|----------|---------|
| `ws://host/desk/ws/notifications/` | `NotificationConsumer` | Real-time notification push (server → client) |
| `ws://host/desk/ws/chat/<room_id>/` | `ChatConsumer` | Bidirectional live chat messaging |

**Channel Layer:** InMemoryChannelLayer (dev) — use Redis channel layer for production.

---

*Generated on 21 February 2026*
