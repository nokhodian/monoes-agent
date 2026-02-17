## Goal
Deliver a REST API under `webapp` that mirrors all CRM endpoints used by the app, enhances Action/ActionTarget/Collected Profile schemas per your spec, and ships a minimal UI to browse Actions and Targets.

## CRM Usage Survey (Source of Truth)
- Primary interactions found in [APIs.py](file:///Users/morteza/Desktop/monoes/mono-agent/newAgent/src/api/APIs.py) and [api_client.py](file:///Users/morteza/Desktop/monoes/mono-agent/newAgent/src/services/api_client.py). Supporting local persistence in [database.py](file:///Users/morteza/Desktop/monoes/mono-agent/newAgent/src/database/database.py).

## REST Endpoints (Parity + Enhancements)
### Auth & Health
- POST `/api/auth/login` → issue JWT (HS256)
- GET `/api/health` → liveness/readiness

### Actions
- GET `/api/actions` → list; filters: `state`, `type`, `targetPlatform`, `disabled`, `ownerId`, `q`, `page`, `perPage`, `sort`
- GET `/api/actions/{id}` → get specific action (parity of `get_specify_action`)
- POST `/api/actions` → create action (validates enhanced schema)
- PATCH `/api/actions/{id}` → partial update (parity of `update_action_custom`) 
- PATCH `/api/actions/{id}/state` → controlled state transitions (parity of `set_action_state`)
- GET `/api/actions/summary` → counts per status (parity of `get_actions_summary_native`)
- GET `/api/actions/{id}/stats` → execution counters: `actionExecutionCount`, `position`, last run timestamps
- GET `/api/actions/{id}/targets` → list targets for action (enhanced target schema)
- POST `/api/actions/{id}/targets` → add targets (create action targets by personId or link)

### Templates
- GET `/api/templates/{templateId}` → parity of `get_specify_template`

### ActionTargets (replace GraphQL with REST)
- GET `/api/action-targets` → by `actionId`, `status`, `platform`; cursor pagination: `after`, `first`
- PATCH `/api/action-targets/{id}` → update `status`, `commentText`, `metadata`, `lastInteractedAt`
- GET `/api/actions/{id}/collected` → normalized SavedItem array (enhanced Collected Profile schema)

### People (Profiles)
- POST `/api/people:batch` → batch create normalized persons (parity of `POST /rest/batch/people` via `create_people`)
- GET `/api/people/{id}` → normalized person (parity of `get_person`)
- GET `/api/people` → search/filter: `platform`, `username`, `q`, `page`, `perPage`

### Social Lists 
- GET `/api/social-lists` → lists index (parity of `get_saved_list`)
- GET `/api/social-lists/{listId}/items` → list items (parity of `get_social_saved_item`)
- POST `/api/social-lists/{listId}/item` → create one item (parity of `create_social_item`)
- POST `/api/social-lists/{listId}/items` → bulk create items (parity of `create_social_items`)

### Social Users
- PUT `/api/social-users` → bulk update normalized social users (parity of `update_social_users`)

### Messaging Threads
- GET `/api/threads` → optional filters: `actionId`, `confirmed`, `generateReplies` (parity of `get_threads`)
- PUT `/api/threads` → upsert threads with messages (parity of `upsert_threads`)

### System Version
- GET `/api/version` → latest bot version by `platform`, `currentVersion` (parity of `latest_bot_version`)

### Crawler & Configs
- GET `/api/crawler/xpath` → serve crawler configs (replacing mocks)
- GET `/api/configs/{name}` → parity of [APIClient.get_config](file:///Users/morteza/Desktop/monoes/mono-agent/newAgent/src/services/api_client.py#L41-L57)
- POST `/api/configs/extracttest` → parity of [APIClient.extract_test](file:///Users/morteza/Desktop/monoes/mono-agent/newAgent/src/services/api_client.py#L16-L39)
- POST `/api/configs/generate` → parity of [APIClient.generate_config](file:///Users/morteza/Desktop/monoes/mono-agent/newAgent/src/services/api_client.py#L59-L97)

### Merchant Quotas (Optional Parity)
- GET `/api/quotas/merchant` → parity of `get_merchant_quotas` (currently mocked)

## Enhanced Schemas (Authoritative)
### Action
- id: string (UUID)
- createdAt: number (ms since epoch)
- createdBy: string
- ownerId: string
- title: string
- type: BULK_MESSAGING | KEYWORD_SEARCH | PUBLISH_CONTENT | PROFILE_INTERACTION
- state: PENDING | INPROGRESS | PAUSE | DONE
- disabled: boolean
- targetPlatform: TELEGRAM | X | INSTAGRAM | LINKEDIN | EMAIL | TIKTOK
- position: number
- cost: number
- actionExecutionCount: number
- contentSubject: string
- contentMessage: string
- contentBlobURL: string[]
- scheduledDate: string (ISO)
- executionInterval: number (minutes)
- startDate: string (ISO)
- endDate: string (ISO)
- campaignID: string | null
- actionTarget: string[] | ActionTarget[]

### ActionTarget
- id: string (UUID)
- actionId: string (UUID)
- personId: string (UUID)
- platform: TELEGRAM | X | INSTAGRAM | LINKEDIN | EMAIL | TIKTOK
- link: string
- sourceType: LIKE | COMMENT | MESSAGE | PROFILE | SEARCH
- status: PENDING | INPROGRESS | DONE | FAILED
- lastInteractedAt: string (ISO) | null
- commentText: string | null
- metadata: { page?: number, reachedIndex?: number, errorCode?: string, errorMessage?: string, [key: string]: any }

### Collected Profile (SavedItem)
- platform_username: string
- full_name: string
- image_url: string
- contact_details: { type: string, value: string }[]
- website: string
- content_count: number
- follower_count: string | number
- following_count: number
- introduction: string
- is_verified: boolean
- category: string
- job_title: string

## Data Store 
- SQLite via SQLAlchemy: tables for `actions`, `action_targets`, `people`, `social_lists`, `social_list_items`, `threads`
- Mappers to/from legacy where necessary (for UI compatibility)

## Minimal UI
- Pages: Actions list; Action detail (targets + collected data)
- Features: search/filter, paginated tables, state badges, platform chips
- UX: skeleton loaders, accessible keyboard navigation, WCAG AA contrast, hover micro-interactions

## Non-Functional
- Auth: JWT Bearer, role-based middleware
- Pagination: offset for actions, cursor for targets
- Errors: `{ error: { code, message, details }, requestId }` with 400/401/403/404/409/422/500
- CORS: allow `ui` origin

## Implementation Phases
1. Scaffold backend, models, schemas, auth, health
2. Implement parity endpoints (read), enhanced schemas
3. Implement mutations (create/update), pagination, errors
4. Build minimal UI (list/detail), wire filters and data views
5. Add compatibility mappers where existing code expects legacy shapes
6. Tests: unit (schemas/services), integration (routers), UI smoke

## Verification Plan
- Seed fixtures mirroring current CRM shapes
- Validate parity by swapping `RestAPI` base URL to the new service in dev, comparing results for `/actions`, `/actionTargets`, `/people/{id}`

This plan includes all CRM APIs referenced in the codebase and maps them to REST endpoints with your enhanced data models. On approval, I will scaffold `webapp` and begin implementing the backend and UI accordingly.