export default {
  displayName: 'shared-validations',
  preset: '../../../../jest.preset.js',
  testEnvironment: 'node',
  transform: {
    '^.+\\.[tj]s$': ['ts-jest', { tsconfig: '<rootDir>/../../tsconfig.json' }],
  },
  moduleFileExtensions: ['ts', 'js', 'html'],
  coverageDirectory: '../../../../coverage/libs/shared/src/validations',
  moduleNameMapper: {
    '^@libs/shared/validations$': '<rootDir>/date.ts',
  },
};
