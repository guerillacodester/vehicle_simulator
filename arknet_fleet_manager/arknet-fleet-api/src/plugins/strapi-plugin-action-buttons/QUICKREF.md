# Quick Reference - strapi-plugin-action-buttons

## Installation

```bash
npm install strapi-plugin-action-buttons
```

## Enable Plugin

`config/plugins.ts`:

```typescript
export default {
  'action-buttons': {
    enabled: true,
  },
};
```

## Add to Schema

`src/api/[content-type]/content-types/[content-type]/schema.json`:

```json
{
  "button_field_name": {
    "type": "customField",
    "customField": "plugin::action-buttons.button-field",
    "options": {
      "buttonLabel": "Click Me",
      "onClick": "handleMyAction"
    }
  }
}
```

## Create Handler

`src/admin/button-handlers.ts`:

```typescript
declare global {
  interface Window {
    handleMyAction: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => void;
  }
}

window.handleMyAction = async (fieldName, fieldValue, onChange) => {
  console.log('Button clicked!', fieldName, fieldValue);
  
  // Your logic here
  
  if (onChange) {
    onChange({ 
      clicked: true, 
      timestamp: new Date().toISOString() 
    });
  }
};

export {};
```

## Load Handler

`src/admin/app.tsx`:

```typescript
import './button-handlers';

export default {
  config: { locales: [] },
  bootstrap(app) {},
};
```

## Build & Run

```bash
npm run build
npm run develop
```

## Common Patterns

### API Call

```typescript
window.handleAPI = async (fieldName, fieldValue, onChange) => {
  const token = localStorage.getItem('jwtToken');
  const result = await fetch('/api/endpoint', {
    headers: { 'Authorization': `Bearer ${token}` }
  }).then(r => r.json());
  
    if (onChange) onChange({ result });
};
```

### File Upload

```typescript
window.handleUpload = async (fieldName, fieldValue, onChange) => {
};
```

File Upload

```typescript
window.handleUpload = async (fieldName, fieldValue, onChange) => {
  const input = document.createElement('input');
  input.type = 'file';
  input.onchange = (e) => {
    const file = e.target.files[0];
    // Process file
    if (onChange) onChange({ fileName: file.name });
  };
  input.click();
};
```

### Confirmation

```typescript
window.handleConfirm = async (fieldName, fieldValue, onChange) => {
  const confirmed = confirm('Are you sure?');
  if (!confirmed) return;
  
  // Proceed with action
};
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Button doesn't appear | Run `npm run build` and hard refresh (Ctrl+Shift+R) |
| Handler not found | Check handler name matches exactly (case-sensitive) |
| Changes not applying | Restart dev server: `npm run develop` |
| TypeScript errors | Import handlers in app.tsx: `import './button-handlers'` |

## Field Type

**Reference:** `plugin::action-buttons.button-field`  
**Storage:** `json`  
**Required Options:** None (buttonLabel and onClick are optional)

## Handler Signature

```typescript
type ButtonHandler = (
  fieldName: string,           // Schema field name
  fieldValue: any,              // Current stored value
  onChange?: (value: any) => void  // Update function
) => void | Promise<void>;
```

## Multiple Buttons

```json
{
  "button1": {
    "customField": "plugin::action-buttons.button-field",
    "options": { "buttonLabel": "Action 1", "onClick": "handler1" }
  },
  "button2": {
    "customField": "plugin::action-buttons.button-field",
    "options": { "buttonLabel": "Action 2", "onClick": "handler2" }
  }
}
```

## More Info

- Full docs: `README.md`
- Examples: `EXAMPLES.ts`
- Installation: `INSTALLATION.md`
