import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: 'http://localhost:1337/graphql',
  documents: ['src/**/*.{ts,tsx}', 'src/lib/graphql/**/*.ts'],
  generates: {
    './src/lib/graphql/__generated__/': {
      preset: 'client',
      plugins: [],
      presetConfig: {
        gqlTagName: 'gql',
      }
    },
    './src/lib/graphql/__generated__/urql.ts': {
      plugins: [
        'typescript',
        'typescript-operations',
        'typescript-urql'
      ],
      config: {
        withHooks: true,
        withComponent: false,
        withHOC: false
      }
    }
  },
  ignoreNoDocuments: true,
};

export default config;
