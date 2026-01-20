import { githubUsername } from '../username';

describe('githubUsername', () => {
  const suffix = '_LinkedIn';

  describe('successful username formatting', () => {
    it('should append suffix to username without suffix', () => {
      expect(githubUsername('octocat', suffix)).toBe('octocat_LinkedIn');
    });

    it('should return username unchanged if it already ends with suffix', () => {
      expect(githubUsername('octocat_LinkedIn', suffix)).toBe('octocat_LinkedIn');
    });

    it('should handle usernames with underscores', () => {
      expect(githubUsername('john_doe', suffix)).toBe('john_doe_LinkedIn');
    });

    it('should handle usernames with hyphens', () => {
      expect(githubUsername('john-doe', suffix)).toBe('john-doe_LinkedIn');
    });

    it('should handle usernames with numbers', () => {
      expect(githubUsername('user123', suffix)).toBe('user123_LinkedIn');
    });

    it('should trim whitespace from username', () => {
      expect(githubUsername('  octocat  ', suffix)).toBe('octocat_LinkedIn');
    });

    it('should trim whitespace from suffix', () => {
      expect(githubUsername('octocat', '  _LinkedIn  ')).toBe('octocat_LinkedIn');
    });

    it('should handle complex usernames', () => {
      expect(githubUsername('test_user-123', suffix)).toBe('test_user-123_LinkedIn');
    });
  });

  describe('error handling - empty/invalid suffix', () => {
    it('should throw error if suffix is empty string', () => {
      expect(() => githubUsername('octocat', '')).toThrow(
        'Suffix is required and cannot be empty'
      );
    });

    it('should throw error if suffix is only whitespace', () => {
      expect(() => githubUsername('octocat', '   ')).toThrow(
        'Suffix is required and cannot be empty'
      );
    });

    it('should throw error if suffix is undefined', () => {
      expect(() => githubUsername('octocat', undefined as any)).toThrow(
        'Suffix is required and cannot be empty'
      );
    });

    it('should throw error if suffix is null', () => {
      expect(() => githubUsername('octocat', null as any)).toThrow(
        'Suffix is required and cannot be empty'
      );
    });
  });

  describe('error handling - empty/invalid username', () => {
    it('should throw error if username is empty string', () => {
      expect(() => githubUsername('', suffix)).toThrow(
        'Username is required and cannot be empty'
      );
    });

    it('should throw error if username is only whitespace', () => {
      expect(() => githubUsername('   ', suffix)).toThrow(
        'Username is required and cannot be empty'
      );
    });

    it('should throw error if username is undefined', () => {
      expect(() => githubUsername(undefined as any, suffix)).toThrow(
        'Username is required and cannot be empty'
      );
    });

    it('should throw error if username is null', () => {
      expect(() => githubUsername(null as any, suffix)).toThrow(
        'Username is required and cannot be empty'
      );
    });
  });

  describe('error handling - malformed username', () => {
    it('should throw error if suffix appears in the middle of username', () => {
      expect(() => githubUsername('octo_LinkedIn_cat', suffix)).toThrow(
        'Username "octo_LinkedIn_cat" contains suffix "_LinkedIn" in an incorrect position. ' +
        'Suffix must only appear at the end.'
      );
    });

    it('should throw error if suffix appears at the beginning', () => {
      expect(() => githubUsername('_LinkedIn_octocat', suffix)).toThrow(
        'Username "_LinkedIn_octocat" contains suffix "_LinkedIn" in an incorrect position. ' +
        'Suffix must only appear at the end.'
      );
    });

    it('should throw error if username has multiple occurrences of suffix', () => {
      expect(() => githubUsername('_LinkedIn_test_LinkedIn', suffix)).toThrow(
        'Username "_LinkedIn_test_LinkedIn" contains suffix "_LinkedIn" in an incorrect position. ' +
        'Suffix must only appear at the end.'
      );
    });
  });

  describe('edge cases', () => {
    it('should handle single character username', () => {
      expect(githubUsername('a', suffix)).toBe('a_LinkedIn');
    });

    it('should handle very long usernames', () => {
      const longUsername = 'a'.repeat(39); // GitHub max is 39 chars
      expect(githubUsername(longUsername, suffix)).toBe(`${longUsername}_LinkedIn`);
    });

    it('should handle different suffix formats', () => {
      expect(githubUsername('octocat', '-suffix')).toBe('octocat-suffix');
      expect(githubUsername('octocat', '_company')).toBe('octocat_company');
      expect(githubUsername('octocat', 'Suffix')).toBe('octocatSuffix');
    });

    it('should be case-sensitive', () => {
      expect(githubUsername('octocat_linkedin', '_LinkedIn')).toBe('octocat_linkedin_LinkedIn');
      expect(githubUsername('octocat_LinkedIn', '_linkedin')).toBe('octocat_LinkedIn_linkedin');
    });
  });
});
