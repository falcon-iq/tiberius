export default {
  displayName: 'shared-ui',
  preset: '../../../../jest.preset.js',
  testEnvironment: 'jsdom',
  passWithNoTests: true,
  transform: {
    '^.+\\.[tj]sx?$': [
      '@swc/jest',
      {
        jsc: {
          parser: { syntax: 'typescript', tsx: true },
          transform: { react: { runtime: 'automatic' } },
        },
      },
    ],
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx'],
  coverageDirectory: '../../../../coverage/libs/shared/src/ui',
};
