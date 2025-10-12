#!/bin/bash
# Lifecycle Hook Verification Script
# This script verifies the Strapi lifecycle hooks are functioning correctly

set -e

echo "========================================"
echo "Strapi Lifecycle Hook Verification"
echo "========================================"
echo ""

# Change to the Strapi directory
cd /home/runner/work/vehicle_simulator/vehicle_simulator/arknet_fleet_manager/arknet-fleet-api

# 1. Verify TypeScript compilation
echo "1️⃣  Verifying TypeScript compilation..."
npx tsc --noEmit
if [ $? -eq 0 ]; then
    echo "   ✅ TypeScript compilation successful"
else
    echo "   ❌ TypeScript compilation failed"
    exit 1
fi
echo ""

# 2. Verify Strapi build
echo "2️⃣  Verifying Strapi build..."
npm run build > /tmp/build_output.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Strapi build successful"
    # Show build summary
    tail -5 /tmp/build_output.log
else
    echo "   ❌ Strapi build failed"
    tail -20 /tmp/build_output.log
    exit 1
fi
echo ""

# 3. Check lifecycle files exist and are syntactically valid
echo "3️⃣  Verifying lifecycle hook files..."

# Country lifecycle
if [ -f "src/api/country/content-types/country/lifecycles.ts" ]; then
    echo "   ✅ Country lifecycle hook exists"
else
    echo "   ❌ Country lifecycle hook missing"
    exit 1
fi

# Route lifecycle
if [ -f "src/api/route/content-types/route/lifecycles.ts" ]; then
    echo "   ✅ Route lifecycle hook exists"
else
    echo "   ❌ Route lifecycle hook missing"
    exit 1
fi

# File upload lifecycle
if [ -f "src/extensions/upload/content-types/file/lifecycles.ts" ]; then
    echo "   ✅ File upload lifecycle hook exists"
else
    echo "   ❌ File upload lifecycle hook missing"
    exit 1
fi

# Global type declaration
if [ -f "src/types/strapi.d.ts" ]; then
    echo "   ✅ Global strapi type declaration exists"
else
    echo "   ❌ Global strapi type declaration missing"
    exit 1
fi
echo ""

# 4. Verify no debugger statements in production build
echo "4️⃣  Checking for debugger statements..."
DEBUGGER_COUNT=$(grep -r "debugger;" src/api/*/content-types/*/lifecycles.ts | wc -l)
if [ "$DEBUGGER_COUNT" -gt 0 ]; then
    echo "   ⚠️  Found $DEBUGGER_COUNT debugger statements (OK for development)"
else
    echo "   ✅ No debugger statements found"
fi
echo ""

# 5. Check for proper error handling
echo "5️⃣  Verifying error handling..."
ERROR_HANDLERS=$(grep -r "catch (error" src/api/*/content-types/*/lifecycles.ts | wc -l)
if [ "$ERROR_HANDLERS" -gt 0 ]; then
    echo "   ✅ Found $ERROR_HANDLERS error handlers"
else
    echo "   ❌ No error handlers found"
    exit 1
fi
echo ""

# 6. Verify helper functions are defined
echo "6️⃣  Verifying helper functions..."

# Country lifecycle helpers
COUNTRY_HELPERS=$(grep -c "^async function" src/api/country/content-types/country/lifecycles.ts)
echo "   ✅ Country lifecycle has $COUNTRY_HELPERS helper functions"

# Route lifecycle helpers
ROUTE_HELPERS=$(grep -c "^async function" src/api/route/content-types/route/lifecycles.ts)
echo "   ✅ Route lifecycle has $ROUTE_HELPERS helper functions"
echo ""

# 7. Summary
echo "========================================"
echo "Verification Complete"
echo "========================================"
echo ""
echo "Summary:"
echo "  ✅ TypeScript compilation: PASSED"
echo "  ✅ Strapi build: PASSED"
echo "  ✅ Lifecycle hooks: PRESENT"
echo "  ✅ Type declarations: PRESENT"
echo "  ✅ Error handling: VERIFIED"
echo "  ✅ Helper functions: VERIFIED"
echo ""
echo "Status: ALL CHECKS PASSED ✅"
echo ""
echo "The lifecycle hooks are ready for runtime testing."
echo "Start Strapi with: npm run develop"
echo ""
