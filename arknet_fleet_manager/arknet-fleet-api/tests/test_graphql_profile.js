/**
 * Test script to verify GraphQL profile manager integration
 * Tests that user profile and access tier are properly loaded via middleware
 */

const fetch = require('node-fetch');

const GRAPHQL_URL = 'http://localhost:1337/graphql';
const LOGIN_URL = 'http://localhost:1337/api/auth/local';

// Test credentials - using seeded test users from seed_test_users.js
const TEST_USER = {
  identifier: 'viewer_user', // or viewer@test.com
  password: 'Test123!',
};

async function login() {
  console.log('\n🔐 Logging in...');
  const response = await fetch(LOGIN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(TEST_USER),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Login failed: ${error}`);
  }

  const data = await response.json();
  console.log(`✅ Logged in as: ${data.user.username} (ID: ${data.user.id})`);
  return data.jwt;
}

async function testGraphQLMe(jwt) {
  console.log('\n📊 Testing GraphQL "me" query with tier field...');
  
  const query = `
    query {
      me {
        id
        username
        email
        tier
      }
    }
  `;

  const response = await fetch(GRAPHQL_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${jwt}`,
    },
    body: JSON.stringify({ query }),
  });

  const result = await response.json();
  
  console.log('📄 Full GraphQL response:', JSON.stringify(result, null, 2));
  
  if (result.errors) {
    console.error('❌ GraphQL errors:', JSON.stringify(result.errors, null, 2));
    return false;
  }

  console.log('✅ GraphQL data:', JSON.stringify(result.data, null, 2));
  
  if (result.data?.me?.tier) {
    console.log(`✅ Tier successfully loaded: ${result.data.me.tier}`);
    return true;
  } else {
    console.log('⚠️  Tier field is null or missing');
    return false;
  }
}

async function testGraphQLUsersQuery(jwt) {
  console.log('\n📊 Testing GraphQL users query with tier field...');
  
  const query = `
    query {
      usersPermissionsUsers(pagination: { limit: 1 }) {
        data {
          id
          attributes {
            username
            email
          }
        }
      }
    }
  `;

  const response = await fetch(GRAPHQL_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${jwt}`,
    },
    body: JSON.stringify({ query }),
  });

  const result = await response.json();
  
  if (result.errors) {
    console.error('❌ GraphQL errors:', JSON.stringify(result.errors, null, 2));
    return false;
  }

  console.log('✅ GraphQL response:', JSON.stringify(result.data, null, 2));
  return true;
}

async function testRestMe(jwt) {
  console.log('\n📊 Testing REST API /api/users/me...');
  
  const response = await fetch('http://localhost:1337/api/users/me', {
    headers: {
      'Authorization': `Bearer ${jwt}`,
    },
  });

  const result = await response.json();
  
  if (!response.ok) {
    console.error('❌ REST API error:', result);
    return false;
  }

  console.log('✅ REST response:', JSON.stringify(result, null, 2));
  
  if (result.profile?.access_tier) {
    console.log(`✅ Profile with tier loaded via REST: ${result.profile.access_tier.name}`);
    return true;
  } else {
    console.log('⚠️  Profile or access_tier not populated in REST response');
    return false;
  }
}

async function main() {
  try {
    console.log('🧪 Testing Profile Manager Integration');
    console.log('=====================================');

    // Login
    const jwt = await login();

    // Test GraphQL
    const graphqlMeSuccess = await testGraphQLMe(jwt);
    await testGraphQLUsersQuery(jwt);

    // Test REST
    const restSuccess = await testRestMe(jwt);

    // Summary
    console.log('\n📋 Test Summary');
    console.log('=====================================');
    console.log(`GraphQL "me" query with tier: ${graphqlMeSuccess ? '✅ PASS' : '❌ FAIL'}`);
    console.log(`REST API /users/me with profile: ${restSuccess ? '✅ PASS' : '❌ FAIL'}`);

    if (graphqlMeSuccess && restSuccess) {
      console.log('\n🎉 All tests passed!');
      process.exit(0);
    } else {
      console.log('\n⚠️  Some tests failed. Check logs above.');
      process.exit(1);
    }

  } catch (error) {
    console.error('\n❌ Test failed with error:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

main();
