# Architecture Overview

## How It Works

```text
┌─────────────────────────────────────────────────────────────────┐
│                    STRAPI ADMIN PANEL                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          Content Type: Article                           │  │
│  │                                                          │  │
│  │  Title: [My Article______________]                       │  │
│  │                                                          │  │
│  │  Send Email:  ┌──────────────────┐                      │  │
│  │               │ 📧 Send Email ▶  │  ← Custom Button     │  │
│  │               └──────────────────┘                       │  │
│  │               Last Action:                               │  │
│  │               {                                          │  │
│  │                 "emailSent": true,                       │  │
│  │                 "timestamp": "2025-10-24T10:30:00Z"      │  │
│  │               }                                          │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Click Event
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               CustomFieldButton Component                       │
│                                                                 │
│  1. Read button configuration:                                 │
│     - buttonLabel: "📧 Send Email"                             │
│     - onClick: "handleSendEmail"                               │
│                                                                 │
│  2. Lookup handler on window object:                           │
│     window["handleSendEmail"]                                  │
│                                                                 │
│  3. Call handler with parameters:                              │
│     handler(fieldName, fieldValue, onChange)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│          Handler Function (button-handlers.ts)                  │
│                                                                 │
│  window.handleSendEmail = async (                              │
│    fieldName,    // "send_email"                               │
│    fieldValue,   // { emailSent: true, ... }                   │
│    onChange      // Function to update field                   │
│  ) => {                                                         │
│    // 1. Your custom logic                                     │
│    const result = await fetch('/api/send-email', ...);         │
│                                                                 │
│    // 2. Update field metadata                                 │
│    onChange({                                                   │
│      emailSent: true,                                           │
│      timestamp: new Date().toISOString(),                       │
│      status: 'success'                                          │
│    });                                                          │
│  };                                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Flow                                    │
│                                                                 │
│  1. onChange() updates React state                             │
│  2. State is stored in field value                             │
│  3. User saves entry                                           │
│  4. Data persists to database as JSON                          │
│  5. Next time entry loads, fieldValue contains saved data      │
└─────────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```text
Strapi Admin Panel
│
├── Content Manager
│   │
│   └── Edit View (Article)
│       │
│       ├── Field: Title (string)
│       │
│       └── Field: send_email (customField)
│           │
│           └── CustomFieldButton Component
│               │
│               ├── Button (Strapi Design System)
│               │
│               └── Metadata Display
│
└── Window Object
    │
    └── Global Handlers
        ├── handleSendEmail
        ├── handleUploadCSV
        ├── handleGenerateReport
        └── ... (user-defined)
```

## Data Flow Diagram

```text
Schema (JSON)              Plugin Registration         Admin Component
─────────────              ────────────────────        ───────────────
{                                                       CustomFieldButton
  "send_email": {           server/register.ts:        │
    "type": "customField",  strapi.customFields        ├─ Reads options
    "customField":          .register({                │  - buttonLabel
    "plugin::action-        name: 'button-field',      │  - onClick
    buttons.button-field",  type: 'json'               │
    "options": {            })                         ├─ Renders button
      "buttonLabel":                                   │
      "📧 Send Email",      admin/index.ts:            ├─ On click:
      "onClick":            app.customFields           │  - Find handler
      "handleSendEmail"     .register({                │  - Call handler
    }                       name: 'button-field',      │  - Pass callbacks
  }                         components: {              │
}                           Input: CustomFieldButton   └─ Display metadata
                            }                             
                            })
                                    │
                                    │
                                    ▼
                            Handler Function
                            ────────────────
                            window.handleSendEmail
                            │
                            ├─ Your custom logic
                            ├─ API calls
                            ├─ File operations
                            ├─ External services
                            │
                            └─ onChange({ metadata })
                                    │
                                    ▼
                            Database (PostgreSQL)
                            ─────────────────────
                            {
                              "emailSent": true,
                              "timestamp": "...",
                              "status": "success"
                            }
```

## Plugin Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                  strapi-plugin-action-buttons                │
│                                                              │
│  ┌──────────────────────┐    ┌───────────────────────────┐  │
│  │  Server Side         │    │  Admin Side               │  │
│  │  (Node.js)           │    │  (React/TypeScript)       │  │
│  │                      │    │                           │  │
│  │  register.ts         │    │  index.ts                 │  │
│  │  │                   │    │  │                        │  │
│  │  └─ Register custom  │    │  └─ Register custom       │  │
│  │     field type       │    │     field in admin        │  │
│  │     - Name           │    │     - Component           │  │
│  │     - Type: json     │    │     - Configuration UI    │  │
│  │                      │    │                           │  │
│  └──────────────────────┘    │  CustomFieldButton.tsx    │  │
│                              │  │                        │  │
│                              │  ├─ Button UI             │  │
│                              │  ├─ Handler execution     │  │
│                              │  └─ Metadata display      │  │
│                              │                           │  │
│                              └───────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                              │
                              │ Used by
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                   Your Strapi Project                        │
│                                                              │
│  ┌─────────────────────┐    ┌────────────────────────────┐  │
│  │  Content Type       │    │  Admin Customization       │  │
│  │  Schema             │    │                            │  │
│  │                     │    │  button-handlers.ts        │  │
│  │  Uses:              │    │  │                         │  │
│  │  plugin::action-    │    │  ├─ handleSendEmail       │  │
│  │  buttons.button-    │    │  ├─ handleUploadCSV       │  │
│  │  field              │    │  ├─ handleGenerateReport  │  │
│  │                     │    │  └─ ... (your handlers)   │  │
│  │  Configures:        │    │                            │  │
│  │  - buttonLabel      │    │  app.tsx                   │  │
│  │  - onClick          │    │  │                         │  │
│  │                     │    │  └─ import handlers        │  │
│  └─────────────────────┘    └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Execution Flow

```text
1. User Opens Entry
   └─> Strapi loads content type schema
       └─> Finds custom field: plugin::action-buttons.button-field
           └─> Loads CustomFieldButton component
               └─> Reads options: { buttonLabel, onClick }
                   └─> Renders button with label

2. User Clicks Button
   └─> CustomFieldButton onClick handler
       └─> Looks up window[onClick]
           └─> Finds handler function
               └─> Calls: handler(fieldName, fieldValue, onChange)

3. Handler Executes
   └─> Your custom logic runs
       ├─> API calls
       ├─> File operations
       ├─> External services
       └─> Calls onChange({ metadata })

4. Field Updates
   └─> onChange callback updates React state
       └─> UI shows new metadata
           └─> User saves entry
               └─> Metadata persists to database

5. Next Load
   └─> Field loads with saved metadata
       └─> Previous actions visible
           └─> Handler can access history via fieldValue
```

## Security Model

```text
┌──────────────────────────────────────────────────────────────┐
│                     Security Boundaries                      │
│                                                              │
│  Browser Context (Admin Panel)                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Your Handler Code                                     │  │
│  │  - Has access to localStorage (auth tokens)           │  │
│  │  - Can call Strapi APIs                               │  │
│  │  - Can access window/document                         │  │
│  │  - Runs in admin user's browser                       │  │
│  └────────────────────────────────────────────────────────┘  │
│                              │                               │
│                              │ HTTP/HTTPS                    │
│                              ▼                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Strapi Backend                                        │  │
│  │  - Standard authentication required                    │  │
│  │  - Standard authorization applies                      │  │
│  │  - Plugin only stores JSON data                        │  │
│  │  - No server-side execution                            │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

Note: Handlers run in browser with admin privileges.
Always validate and sanitize data before sending to backend.
```

## Extension Points

```text
You can customize:

1. Button Labels
   └─> Any text, emojis, unicode

2. Handler Functions
   └─> Any JavaScript/TypeScript code
       ├─> Async operations
       ├─> API calls
       ├─> File operations
       └─> Third-party integrations

3. Metadata Structure
   └─> Any JSON-serializable data
       ├─> Simple values
       ├─> Nested objects
       ├─> Arrays
       └─> Complex structures

4. UI Feedback
   └─> Handler controls user experience
       ├─> alerts/confirms
       ├─> DOM manipulation
       ├─> Progress indicators
       └─> Custom modals
```
