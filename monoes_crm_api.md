# Monoes CRM API Documentation

This document outlines the API endpoints implemented from Monoes CRM that interact with the current application. It details the data types, input/output structures, and authentication methods. This documentation is intended to serve as a reference for designing a new RESTful API system to replace the current CRM integration.

## Base URL

```
https://monoes.me/rest
```

## Authentication

All API requests require an Authorization header with a Bearer token.

```http
Authorization: Bearer <YOUR_TOKEN>
```

## Endpoints

### 1. Get Actions

Fetches a list of actions, optionally filtered by state.

- **Endpoint**: `/actions`
- **Method**: `GET`
- **Query Parameters**:
    - `state` (optional): Filter by action state (`PENDING`, `IN_PROGRESS`, `DONE`).
    - `disabled` (optional): Filter by disabled status (default: `false`).

#### Response Structure

```json
{
  "data": {
    "actions": [
      {
        "id": "string",
        "createdAt": "string (ISO 8601)",
        "type": "string",
        "status": "string (ASSIGNED, IN_PROGRESS, PAUSED, PENDING, DONE)",
        "title": "string",
        "createdBy": {
          "name": "string"
        },
        "target": "string",
        "contentType": "string",
        "jobs": [],
        "maxResultsCount": "integer",
        "content": "string",
        "messageSubject": "string",
        "keywords": "string",
        "scheduledDate": "string",
        "mediaURL": "string",
        "locationTag": "string",
        "lastExecutedAt": "string",
        "completedAt": "string",
        "disabled": "boolean",
        "ownerId": "string",
        "position": "integer",
        "noMorePages": "boolean",
        "updatedAt": "string",
        "deletedAt": "string",
        "aiUsed": "boolean"
      }
    ],
    "totalCount": "integer"
  }
}
```

### 2. Get Action Targets

Fetches targets associated with a specific action.

- **Endpoint**: `/actionTargets`
- **Method**: `GET`
- **Query Parameters**:
    - `actionId`: The ID of the action.
    - `first`: Number of items to return (limit).
    - `after`: Cursor for pagination.

#### Response Structure

```json
{
  "data": {
    "actionTargets": [
      {
        "actionId": "string",
        "personId": "string",
        "person": {
            // See Person Data Structure below
        },
        "company": {
            // Company details if applicable
        },
        "opportunity": {
            // Opportunity details if applicable
        }
      }
    ],
    "pageInfo": {
      "hasNextPage": "boolean",
      "endCursor": "string"
    }
  }
}
```

### 3. Get Person

Fetches details of a specific person.

- **Endpoint**: `/people/{personId}`
- **Method**: `GET`
- **Path Parameters**:
    - `personId`: The ID of the person.

#### Response Structure

```json
{
  "data": {
    "person": {
      // See Person Data Structure below
    }
  }
}
```

### 4. Update Action

Updates an existing action.

- **Endpoint**: `/actions/{actionId}`
- **Method**: `PATCH`
- **Path Parameters**:
    - `actionId`: The ID of the action.
- **Body**: JSON object with fields to update.

#### Request Body Example

```json
{
  "status": "DONE",
  "state": "DONE"
}
```

### 5. GraphQL Query

Executes a GraphQL query, primarily used for efficient fetching of action targets with nested person data.

- **Endpoint**: `/graphql`
- **Method**: `POST`
- **Body**: JSON object containing the query and variables.

#### Request Body Example

```json
{
  "query": "query ActionTargets($actionId: String!, $first: Int!, $after: String) { ... }",
  "variables": {
    "actionId": "...",
    "first": 100,
    "after": "..."
  }
}
```

## Data Types

### Person Data Structure

The `Person` object contains detailed information about a contact, including social media profiles.

```json
{
  "id": "string",
  "name": {
    "firstName": "string",
    "lastName": "string"
  },
  "emails": {
    "primaryEmail": "string",
    "additionalEmails": ["string"]
  },
  "phones": {
    "primaryPhoneNumber": "string",
    "additionalPhones": ["string"]
  },
  "city": "string",
  "avatarUrl": "string",
  "position": "string",
  "createdAt": "string (ISO 8601)",
  "updatedAt": "string (ISO 8601)",
  "companyId": "string",
  "createdBy": {
    "name": "string"
  },
  "jobTitle": "string",
  "searchVector": "string",
  "deletedAt": "string",
  
  // Social Media Links & Data
  "linkedinLink": { "primaryLinkUrl": "string" },
  "linkedinIntro": "string",
  "linkedinFollowerCount": "integer",
  "linkedinPosition": "string",
  
  "instaLink": { "primaryLinkUrl": "string" },
  "instaCategory": "string",
  "instaIntro": "string",
  "instaIsVerified": "boolean",
  "instaFollowerCount": "integer",
  
  "tiktokLink": { "primaryLinkUrl": "string" },
  "tiktokCategory": "string",
  "tiktokIntro": "string",
  "tiktokIsVerified": "boolean",
  "tiktokFollowerCount": "integer",
  
  "xLink": { "primaryLinkUrl": "string" },
  "xCategory": "string",
  "xIntro": "string",
  "xIsVerified": "boolean",
  "xFollowerCount": "integer",
  
  "telegramLink": { "primaryLinkUrl": "string" }
}
```

### Action Data Structure (Legacy Transformation)

The application transforms the raw API response into a legacy format for internal use.

```json
{
  "id": "string",
  "createdAt": "integer (timestamp in ms)",
  "type": "string",
  "state": "string (PENDING, INPROGRESS, PAUSE, DONE)",
  "title": "string",
  "createdBy": "string",
  "execProps": {
    "source": "string",
    "sourceType": "string",
    "jobs": [],
    "maxResultsCount": "integer",
    "resultsCount": "integer",
    "failedInvites": [],
    "inviteesCount": "integer",
    "reachedIndex": "integer",
    "failedProfileSearches": [],
    "profilesCount": "integer",
    "failedMessages": [],
    "recipientsCount": "integer",
    "failedItems": [],
    "itemsCount": "integer",
    "requiredQuotas": "integer",
    "currentStage": "string",
    "reachedSubIndex": "integer"
  },
  "props": {
    "listId": "string",
    "selectedListItems": [],
    "emails": [],
    "campaignId": "string",
    "messageText": "string",
    "messageSubject": "string",
    "messageTemplateId": "integer",
    "keyword": "string",
    "maxResultsCount": "integer",
    "scheduledDate": "string",
    "media": [
      {
        "url": "string",
        "type": "string (VIDEO, IMAGE)",
        "effect": "string",
        "customRatio": "string"
      }
    ],
    "text": "string",
    "locationTag": "string",
    "target": "string",
    "startDate": "string",
    "endDate": "string",
    "pollInterval": "integer",
    "maxContentCount": "integer",
    "commentText": "string",
    "searches": []
  },
  "lastExecutedAt": "string",
  "completedAt": "string",
  "disabled": "boolean",
  "ownerId": "string",
  "position": "integer",
  "noMorePages": "boolean",
  "updatedAt": "string",
  "deletedAt": "string",
  "aiUsed": "boolean"
}
```

## Legacy Mapping Logic

### Person Mapping
The system maps the detailed `Person` object to a simplified "Legacy" format for backward compatibility.
- **Social Platforms**: Iterates through `["insta", "tiktok", "x", "linkedin"]` and maps them to a uniform structure under `platforms`.
- **Company Data**: Flattens nested company object fields into top-level keys like `company_name`, `company_domain`, etc.

### Action Mapping
- **Timestamps**: Converts ISO 8601 strings to milliseconds timestamps.
- **State**: Maps API statuses (`ASSIGNED`, `IN_PROGRESS`) to GUI states (`PENDING`, `INPROGRESS`).
- **Media**: Parses `mediaURL` and `contentType` into a `media` array with type detection (VIDEO/IMAGE).
