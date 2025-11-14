# Installation & Usage Guide

## Table of Contents

1. [Installing from npm](#installing-from-npm)
2. [Installing from Local Source](#installing-from-local-source)
3. [Publishing to npm](#publishing-to-npm)
4. [Quick Start Tutorial](#quick-start-tutorial)
5. [Testing the Plugin](#testing-the-plugin)

---

## Installing from npm

Once published to npm, users can install your plugin:

```bash
npm install strapi-plugin-action-buttons
# or
yarn add strapi-plugin-action-buttons
# or
pnpm add strapi-plugin-action-buttons
```

Then enable it in `config/plugins.ts`:

```typescript
export default {
  'action-buttons': {
    enabled: true,
  },
};
```

---

## Installing from Local Source

### For Development/Testing

If you want to test the plugin locally before publishing:

#### Method 1: npm link

In the plugin directory:

```bash
cd src/plugins/strapi-plugin-action-buttons
npm link
```

In your Strapi project:

```bash
npm link strapi-plugin-action-buttons
```

#### Method 2: Local Path

In your Strapi project's `package.json`:

```json
{
  "dependencies": {
    "strapi-plugin-action-buttons": "file:./src/plugins/strapi-plugin-action-buttons"
  }
}
```

Then run:

```bash
npm install
```

#### Method 3: Direct Plugin Folder (Current Setup)

Keep the plugin in `src/plugins/` and enable in `config/plugins.ts`:

```typescript
export default {
  'action-buttons': {
    enabled: true,
    resolve: './src/plugins/strapi-plugin-action-buttons'
  },
};
```

**⚠️ CRITICAL:** You MUST build the plugin before it will work:

```bash
cd src/plugins/strapi-plugin-action-buttons
npm install
npm run build
```

The plugin requires compiled files in the `dist/` folder. If you see errors like "Could not find Custom Field" or the custom field doesn't appear in the Content-Type Builder, rebuild the plugin.

---

## Publishing to npm

### Prerequisites

1. Create an npm account at <https://www.npmjs.com>
2. Login to npm:

   ```bash
   npm login
   ```

### Pre-publish Checklist

1. **Update package.json** with your information:

   ```json
   {
     "name": "strapi-plugin-action-buttons",
     "author": {
       "name": "Your Name",
       "email": "your.email@example.com"
     },
     "repository": {
       "type": "git",
       "url": "https://github.com/yourusername/strapi-plugin-action-buttons.git"
     }
   }
   ```

2. **Build the plugin**:

   ```bash
   cd src/plugins/strapi-plugin-action-buttons
   npm run build
   ```

3. **Test locally** (see Testing section below)

4. **Update version** in package.json:

   ```json
   {
     "version": "1.0.0"
   }
   ```

### Publishing

```bash
cd src/plugins/strapi-plugin-action-buttons

# First time publishing
npm publish

# For updates
npm version patch  # 1.0.0 -> 1.0.1
npm publish

npm version minor  # 1.0.0 -> 1.1.0
npm publish

npm version major  # 1.0.0 -> 2.0.0
npm publish
```

### Publishing as Scoped Package (Recommended for Organizations)

If you want to publish under your username/organization:

1. Update package.json:

   ```json
   {
     "name": "@yourusername/strapi-plugin-action-buttons"
   }
   ```

2. Publish:

   ```bash
   npm publish --access public
   ```

Users would then install with:

```bash
npm install @yourusername/strapi-plugin-action-buttons
```

---

## Quick Start Tutorial

### Step 1: Install the Plugin

```bash
npm install strapi-plugin-action-buttons
```

### Step 2: Enable in Config

Create or edit `config/plugins.ts`:

```typescript
export default {
  'action-buttons': {
    enabled: true,
  },
};
```

### Step 3: Build the Plugin (If Installing Locally)

If you installed from local source or are developing:

```bash
cd node_modules/strapi-plugin-action-buttons
# OR if in src/plugins:
cd src/plugins/strapi-plugin-action-buttons

npm install
npm run build
```

**Why?** The plugin uses compiled TypeScript files from the `dist/` folder. Without building, Strapi cannot load the plugin.

### Step 3: Add to Content Type

Edit your content type schema (e.g., `src/api/article/content-types/article/schema.json`):

```json
{
  "kind": "collectionType",
  "collectionName": "articles",
  "info": {
    "singularName": "article",
    "pluralName": "articles",
    "displayName": "Article"
  },
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

### Step 4: Create Handler

Create `src/admin/button-handlers.ts`:

```typescript
declare global {
  interface Window {
    handleSendEmail: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => void;
  }
}

window.handleSendEmail = async (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => {
  console.log('Button clicked!', fieldName, fieldValue);
  
  alert('Sending notification...');
  
  // Your custom logic here
  // Example: call an API, process data, etc.
  
  if (onChange) {
    onChange({
      emailSent: true,
      timestamp: new Date().toISOString(),
      status: 'success'
    });
  }
  
  alert('✅ Email sent successfully!');
};

export {};
```

### Step 5: Load Handlers in Admin

Create or edit `src/admin/app.tsx`:

```typescript
import type { StrapiApp } from '@strapi/strapi/admin';
import './button-handlers';

export default {
  config: {
    locales: [],
  },
  bootstrap(app: StrapiApp) {
    console.log('Admin panel bootstrapped with custom handlers');
  },
};
```

### Step 6: Build & Run

```bash
npm run build
npm run develop
```

### Step 7: Test

1. Open admin panel: <http://localhost:1337/admin>
2. Navigate to Content Manager
3. Open an Article entry
4. You should see your "📧 Send Email" button
5. Click it to test the handler

---

## Testing the Plugin

### Manual Testing Checklist

- [ ] Plugin installs without errors
- [ ] Plugin appears in plugins list
- [ ] Custom field appears in Content-Type Builder
- [ ] Can add field to content type
- [ ] Button renders in admin panel
- [ ] Button click triggers handler
- [ ] Handler receives correct parameters
- [ ] onChange updates field value
- [ ] Metadata persists after save
- [ ] Multiple buttons work independently
- [ ] Error messages display correctly
- [ ] Works with both API and plugin content types

### Testing in a Fresh Project

Create a test Strapi project:

```bash
npx create-strapi-app@latest test-project --quickstart
cd test-project
npm install strapi-plugin-action-buttons
```

Follow the Quick Start Tutorial above.

### Common Test Scenarios

1. **Single Button**
   - Add one button field
   - Verify it works

2. **Multiple Buttons**
   - Add 2-3 button fields with different handlers
   - Verify each calls correct handler

3. **Error Handling**
   - Remove handler function
   - Click button
   - Should show helpful error message

4. **Async Operations**
   - Create handler with setTimeout/fetch
   - Verify loading state works
   - Verify completion updates field

5. **Metadata Persistence**
   - Click button to update metadata
   - Save entry
   - Reload page
   - Verify metadata still present

---

## Distribution Checklist

Before sharing or publishing:

- [ ] Update author information in package.json
- [ ] Add repository URL
- [ ] Test installation from npm link
- [ ] Test in fresh Strapi project
- [ ] Verify all examples in README work
- [ ] Check all documentation links
- [ ] Run build command successfully
- [ ] Update CHANGELOG.md
- [ ] Create GitHub release
- [ ] Publish to npm

---

## Need Help?

- Check the main README.md for detailed documentation
- Review the examples in the README
- Check existing GitHub issues
- Create a new issue with reproduction steps

---

## Updating the Plugin

When you make changes and want to publish an update:

1. Make your changes
2. Test thoroughly
3. Update CHANGELOG.md
4. Bump version:

   ```bash
   npm version patch  # or minor/major
   ```

5. Publish:

   ```bash
   npm publish
   ```

6. Create GitHub release with changelog

Users can update with:

```bash
npm update strapi-plugin-action-buttons
```
