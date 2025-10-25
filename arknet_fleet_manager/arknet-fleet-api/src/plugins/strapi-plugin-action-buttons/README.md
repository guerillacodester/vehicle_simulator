# Strapi Plugin Action Buttons

A production-ready Strapi v5 plugin that adds custom action button fields to your content types. Create interactive buttons that trigger custom JavaScript handlers for workflows, API calls, data processing, and more.

[![npm version](https://img.shields.io/npm/v/strapi-plugin-action-buttons.svg)](https://www.npmjs.com/package/strapi-plugin-action-buttons)
[![npm downloads](https://img.shields.io/npm/dm/strapi-plugin-action-buttons.svg)](https://www.npmjs.com/package/strapi-plugin-action-buttons)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🎯 **Custom Action Buttons** - Add clickable buttons to any content type
- 🔧 **Configurable Handlers** - Each button calls a custom JavaScript function
- 🏷️ **Dynamic Labels** - Customize button text per field instance
- 💾 **Metadata Storage** - Store click history and results as JSON
- 🎨 **Built-in UI** - Uses Strapi Design System components
- 📦 **Zero Dependencies** - Only requires Strapi core packages
- 🔌 **Plugin Agnostic** - Works with any content type (API or plugin)
- 🌐 **Global Handlers** - Define handlers in your admin customization

## 📋 Requirements

- **Strapi**: v5.0.0 or higher
- **Node.js**: 18.x, 20.x, or 22.x
- **npm**: 6.0.0 or higher

## 📦 Installation

```bash
# Using npm
npm install strapi-plugin-action-buttons

# Using yarn
yarn add strapi-plugin-action-buttons

# Using pnpm
pnpm add strapi-plugin-action-buttons
```

### Building the Plugin (Important!)

**If installing from source or developing locally**, you MUST build the plugin:

```bash
cd node_modules/strapi-plugin-action-buttons
# OR if in src/plugins:
cd src/plugins/strapi-plugin-action-buttons

npm install
npm run build
```

The plugin uses compiled files in `dist/`. Without building, you'll see errors like:

- "Could not find Custom Field: plugin::action-buttons.action-button"
- Custom field not appearing in Content-Type Builder

## 🚀 Quick Start

### Step 1: Enable the Plugin

Add the plugin to your `config/plugins.js` or `config/plugins.ts`:

```typescript
export default {
  'action-buttons': {
    enabled: true,
  },
};
```

### Step 2: Add Button Field to Content Type

Edit your content type schema (e.g., `src/api/article/content-types/article/schema.json`):

```json
{
  "attributes": {
    "title": {
      "type": "string"
    },
    "send_notification": {
      "type": "customField",
      "customField": "plugin::action-buttons.button-field",
      "options": {
        "buttonLabel": "📧 Send Email",
        "onClick": "handleSendEmail"
      }
    }
  }
}
```

### Step 3: Create Handler Function

Create `src/admin/button-handlers.ts`:

```typescript
declare global {
  interface Window {
    handleSendEmail: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => void;
  }
}

window.handleSendEmail = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  console.log('Send Email clicked!', fieldName, fieldValue);
  
  alert('Sending email...');
  
  // Your custom logic here
  // Call APIs, process data, etc.
  
  // Update field with metadata
  if (onChange) {
    onChange({
      emailSent: true,
      timestamp: new Date().toISOString(),
      status: 'success'
    });
  }
  
  alert('✅ Email sent!');
};

export {};
```

### Step 4: Load Handlers in Admin Panel

Edit `src/admin/app.tsx`:

```typescript
import type { StrapiApp } from '@strapi/strapi/admin';
import './button-handlers';  // ← Load your handlers

export default {
  config: {
    locales: [],
  },
  bootstrap(app: StrapiApp) {
    console.log('Admin panel bootstrapped');
  },
};
```

### Step 5: Restart Strapi

```bash
npm run develop
```

**Note:** If you're developing the plugin locally, make sure you've built it first:

```bash
cd src/plugins/strapi-plugin-action-buttons
npm run build
cd ../../..
npm run develop
```

That's it! Your custom action button is now available in the admin panel.

## 📖 Usage Guide

### Adding Multiple Buttons

You can add multiple buttons with different handlers to the same content type:

```json
{
  "attributes": {
    "upload_csv": {
      "type": "customField",
      "customField": "plugin::action-buttons.button-field",
      "options": {
        "buttonLabel": "📤 Upload CSV",
        "onClick": "handleUploadCSV"
      }
    },
    "generate_report": {
      "type": "customField",
      "customField": "plugin::action-buttons.button-field",
      "options": {
        "buttonLabel": "📊 Generate Report",
        "onClick": "handleGenerateReport"
      }
    },
    "sync_data": {
      "type": "customField",
      "customField": "plugin::action-buttons.button-field",
      "options": {
        "buttonLabel": "🔄 Sync to CRM",
        "onClick": "handleSyncToCRM"
      }
    }
  }
}
```

### Handler Function Signature

All handlers receive three parameters:

```typescript
function handler(
  fieldName: string,           // The schema field name
  fieldValue: any,              // Current stored value (JSON)
  onChange?: (value: any) => void  // Function to update the field
): void | Promise<void>
```

**Parameters:**

- **fieldName**: The name of the field from the schema (e.g., `"send_notification"`)
- **fieldValue**: Current value stored in the field (useful for tracking history)
- **onChange**: Callback to update the field value (data persists when entry is saved)

### Button Configuration Options

Each button field supports these schema options:

```json
{
  "type": "customField",
  "customField": "plugin::action-buttons.button-field",
  "options": {
    "buttonLabel": "Click Me",     // Button text (supports emojis)
    "onClick": "handleMyAction"    // Handler function name
  }
}
```

## 💡 Examples

### Example 1: Send Email Notification

```typescript
window.handleSendEmail = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  const confirmed = confirm('Send email notification?');
  if (!confirmed) return;
  
  try {
    const token = localStorage.getItem('jwtToken');
    const entryId = window.location.pathname.split('/').pop();
    
    const response = await fetch('/api/notifications/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ entryId })
    });
    
    const result = await response.json();
    
    if (onChange) {
      onChange({
        emailSent: true,
        sentAt: new Date().toISOString(),
        recipientCount: result.recipientCount,
        status: 'success'
      });
    }
    
    alert(`✅ Email sent to ${result.recipientCount} recipients`);
  } catch (error) {
    alert('❌ Failed to send email');
    console.error(error);
  }
};
```

### Example 2: Upload and Process CSV

```typescript
window.handleUploadCSV = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.csv';
  
  input.onchange = async (e: any) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (event) => {
      const csvContent = event.target?.result as string;
      const rows = csvContent.split('\n');
      
      if (onChange) {
        onChange({
          uploaded: true,
          fileName: file.name,
          fileSize: file.size,
          rowCount: rows.length - 1,
          uploadedAt: new Date().toISOString()
        });
      }
      
      alert(`✅ Uploaded ${file.name} (${rows.length - 1} rows)`);
    };
    
    reader.readAsText(file);
  };
  
  input.click();
};
```

### Example 3: Sync to External Service

```typescript
window.handleSyncToCRM = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  try {
    const entryId = window.location.pathname.split('/').pop();
    const token = localStorage.getItem('jwtToken');
    
    // Get current entry data
    const entry = await fetch(`/api/articles/${entryId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    }).then(r => r.json());
    
    // Sync to CRM
    const syncResult = await fetch('https://crm-api.example.com/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(entry)
    }).then(r => r.json());
    
    if (onChange) {
      onChange({
        synced: true,
        syncedAt: new Date().toISOString(),
        crmId: syncResult.id,
        status: 'success'
      });
    }
    
    alert(`✅ Synced to CRM (ID: ${syncResult.id})`);
  } catch (error) {
    alert('❌ Sync failed');
    console.error(error);
  }
};
```

## 🎨 Customization

### Button Labels

Button labels support:

- Plain text
- Emojis
- Unicode characters
- Any string value

Examples:

```json
"buttonLabel": "Click Me"
"buttonLabel": "🚀 Deploy"
"buttonLabel": "📧 Send Email"
"buttonLabel": "Process Data"
```

### Storing Metadata

Use the `onChange` callback to store any JSON data:

```typescript
if (onChange) {
  onChange({
    action: 'email_sent',
    timestamp: new Date().toISOString(),
    user: localStorage.getItem('username'),
    result: {
      recipientCount: 5,
      messageIds: ['msg_1', 'msg_2']
    },
    status: 'success'
  });
}
```

This data persists when the entry is saved and is available in subsequent button clicks via the `fieldValue` parameter.

### Tracking Click History

```typescript
window.handleWithHistory = (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  const previousClicks = fieldValue?.clicks || [];
  
  const newClick = {
    timestamp: new Date().toISOString(),
    user: localStorage.getItem('username')
  };
  
  if (onChange) {
    onChange({
      clicks: [...previousClicks, newClick],
      lastClick: newClick.timestamp,
      totalClicks: previousClicks.length + 1
    });
  }
  
  alert(`Total clicks: ${previousClicks.length + 1}`);
};
```

## 🔧 Advanced Usage

### Accessing Entry Data

Get the current entry's data within a handler:

```typescript
window.handleMyAction = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  const entryId = window.location.pathname.split('/').pop();
  const token = localStorage.getItem('jwtToken');
  
  // Fetch full entry with relationships
  const entry = await fetch(`/api/articles/${entryId}?populate=*`, {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(r => r.json());
  
  console.log('Full entry data:', entry);
  
  // Use entry data in your logic
  if (entry.status === 'draft') {
    alert('Cannot perform action on draft entries');
    return;
  }
  
  // Continue with action...
};
```

### Handler Factory Pattern

Create reusable handler factories:

```typescript
function createAPIHandler(endpoint: string, method: string, successMessage: string) {
  return async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
    try {
      const token = localStorage.getItem('jwtToken');
      const entryId = window.location.pathname.split('/').pop();
      
      const response = await fetch(`${endpoint}/${entryId}`, {
        method,
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      const result = await response.json();
      
      if (onChange) {
        onChange({
          executed: true,
          timestamp: new Date().toISOString(),
          result
        });
      }
      
      alert(successMessage);
    } catch (error) {
      alert('Operation failed');
      console.error(error);
    }
  };
}

// Create multiple handlers from factory
window.handlePublish = createAPIHandler('/api/publish', 'POST', '✅ Published!');
window.handleArchive = createAPIHandler('/api/archive', 'POST', '📦 Archived!');
window.handleNotify = createAPIHandler('/api/notify', 'POST', '📧 Notified!');
```

### Progress Indicators

Show loading state during async operations:

```typescript
window.handleWithProgress = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  const button = document.querySelector(`[data-field="${fieldName}"] button`);
  
  if (button) {
    button.textContent = '⏳ Processing...';
    button.disabled = true;
  }
  
  try {
    await performLongOperation();
    
    if (onChange) {
      onChange({ completed: true, timestamp: new Date().toISOString() });
    }
    
    alert('✅ Complete!');
  } finally {
    if (button) {
      button.textContent = 'Process Data';
      button.disabled = false;
    }
  }
};
```

## 🏗️ Use Cases

- **Workflow Automation**: Trigger approvals, send notifications
- **Data Processing**: Import CSV, process raw data, generate reports
- **External Integrations**: Sync to CRM, upload to S3, post to APIs
- **Content Publishing**: Deploy to CDN, invalidate cache, rebuild static site
- **Quality Assurance**: Validate data, check SEO, run tests
- **Notifications**: Email stakeholders, post to Slack, SMS alerts

## 📝 Best Practices

### 1. Always Provide User Feedback

```typescript
// ❌ Bad: Silent execution
window.handleBad = async () => {
  await doSomething();
};

// ✅ Good: Clear feedback
window.handleGood = async (fieldName, fieldValue, onChange) => {
  alert('Processing...');
  try {
    await doSomething();
    alert('✅ Success!');
  } catch (error) {
    alert('❌ Failed!');
  }
};
```

### 2. Confirm Destructive Actions

```typescript
window.handleDelete = async (fieldName, fieldValue, onChange) => {
  const confirmed = confirm('⚠️ This will delete data. Continue?');
  if (!confirmed) return;
  
  // Proceed with deletion...
};
```

### 3. Handle Errors Gracefully

```typescript
window.handleRobust = async (fieldName, fieldValue, onChange) => {
  try {
    const result = await apiCall();
    
    if (onChange) {
      onChange({ success: true, result });
    }
  } catch (error) {
    console.error('Error:', error);
    
    if (onChange) {
      onChange({
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    }
    
    alert('Operation failed. Check console for details.');
  }
};
```

### 4. Store Rich Metadata

```typescript
if (onChange) {
  onChange({
    action: 'data_processed',
    timestamp: new Date().toISOString(),
    user: localStorage.getItem('username'),
    recordCount: 500,
    processingTime: 1234,
    status: 'success'
  });
}
```

## 🐛 Troubleshooting

### Button Doesn't Appear

**Check:**

1. Plugin enabled in `config/plugins.ts`
2. Schema uses correct field reference: `plugin::action-buttons.button-field`
3. Rebuild admin: `npm run build`
4. Hard refresh browser: `Ctrl + Shift + R`

### Handler Not Called

**Check:**

1. Handler name in schema matches function name exactly (case-sensitive)
2. `button-handlers.ts` imported in `src/admin/app.tsx`
3. Handler defined on window: `window.handleMyAction = ...`
4. Check browser console for errors

**Debug in console:**

```javascript
// Should return function
window.handleMyAction
```

### Changes Not Appearing

1. Rebuild admin panel: `npm run build`
2. Clear browser cache
3. Restart dev server: `npm run develop`

## 📚 API Reference

### Custom Field Type

**Name:** `plugin::action-buttons.button-field`

**Storage Type:** `json`

**Schema Options:**

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `buttonLabel` | `string` | No | Button text (default: "Execute Action") |
| `onClick` | `string` | No | Handler function name on window object |

### Handler Function Type

```typescript
type ButtonHandler = (
  fieldName: string,
  fieldValue: any,
  onChange?: (value: any) => void
) => void | Promise<void>;
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built for Strapi v5
- Uses Strapi Design System
- Inspired by real-world workflow automation needs

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/strapi-plugin-action-buttons/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/strapi-plugin-action-buttons/discussions)
- **Email**: <your.email@example.com>

## 🔗 Links

- [npm package](https://www.npmjs.com/package/strapi-plugin-action-buttons)
- [GitHub repository](https://github.com/yourusername/strapi-plugin-action-buttons)
- [Changelog](CHANGELOG.md)
- [Strapi Documentation](https://docs.strapi.io)

---

Made with ❤️ for the Strapi community
