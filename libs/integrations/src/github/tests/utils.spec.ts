import { parseGitHubUser } from '../utils';
import type { ValidateUserResult } from '../auth';

describe('parseGitHubUser', () => {
  describe('successful parsing - common cases', () => {
    it('should parse user with full name and email', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'jdoe_LinkedIn',
        user: {
          login: 'jdoe_LinkedIn',
          id: 12345,
          name: 'John Doe',
          email: 'john.doe@company.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'jdoe',  // LDAP username without suffix
        firstname: 'John',
        lastname: 'Doe',
        email_address: 'john.doe@company.com',
        github_suffix: 'LinkedIn',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should parse user without EMU suffix', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'octocat',
        user: {
          login: 'octocat',
          id: 12345,
          name: 'Octo Cat',
          email: 'octocat@github.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'octocat',
        firstname: 'Octo',
        lastname: 'Cat',
        email_address: 'octocat@github.com',
        github_suffix: null,
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should handle hyphenated last names', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'jsmith_Company',
        user: {
          login: 'jsmith_Company',
          id: 12345,
          name: 'Jane Smith-Johnson',
          email: 'jane@company.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'jsmith',  // LDAP username without suffix
        firstname: 'Jane',
        lastname: 'Smith-Johnson',
        email_address: 'jane@company.com',
        github_suffix: 'Company',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should handle names with special characters', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'user_Org',
        user: {
          login: 'user_Org',
          id: 12345,
          name: "Mary O'Brien",
          email: 'mary@org.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'user',  // LDAP username without suffix
        firstname: 'Mary',
        lastname: "O'Brien",
        email_address: 'mary@org.com',
        github_suffix: 'Org',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });
  });

  describe('edge cases - name parsing', () => {
    it('should handle single-part name (first name only)', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'mononym_LinkedIn',
        user: {
          login: 'mononym_LinkedIn',
          id: 12345,
          name: 'Madonna',
          email: 'madonna@example.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'mononym',  // LDAP username without suffix
        firstname: 'Madonna',
        lastname: '',
        email_address: 'madonna@example.com',
        github_suffix: 'LinkedIn',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should handle multi-part name (three or more parts)', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'jvd_Company',
        user: {
          login: 'jvd_Company',
          id: 12345,
          name: 'Jean-Claude Van Damme',
          email: 'jcvd@company.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'jvd',  // LDAP username without suffix
        firstname: 'Jean-Claude',
        lastname: 'Van Damme',
        email_address: 'jcvd@company.com',
        github_suffix: 'Company',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should handle name with extra whitespace', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'user_Org',
        user: {
          login: 'user_Org',
          id: 12345,
          name: '  John   Doe  ',
          email: 'john@org.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'user',  // LDAP username without suffix
        firstname: 'John',
        lastname: 'Doe',
        email_address: 'john@org.com',
        github_suffix: 'Org',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should handle empty display name', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'user123_LinkedIn',
        user: {
          login: 'user123_LinkedIn',
          id: 12345,
          name: '',
          email: 'user@company.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'user123',  // LDAP username without suffix
        firstname: '',
        lastname: '',
        email_address: 'user@company.com',
        github_suffix: 'LinkedIn',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should handle null display name', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'nullname_Company',
        user: {
          login: 'nullname_Company',
          id: 12345,
          name: null,
          email: 'user@company.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'nullname',  // LDAP username without suffix
        firstname: '',
        lastname: '',
        email_address: 'user@company.com',
        github_suffix: 'Company',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should handle name with only whitespace', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'spacename_Org',
        user: {
          login: 'spacename_Org',
          id: 12345,
          name: '   ',
          email: 'user@org.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'spacename',  // LDAP username without suffix
        firstname: '',
        lastname: '',
        email_address: 'user@org.com',
        github_suffix: 'Org',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });
  });

  describe('edge cases - email handling', () => {
    it('should handle missing email (empty string)', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'noemail_LinkedIn',
        user: {
          login: 'noemail_LinkedIn',
          id: 12345,
          name: 'John Doe',
          email: '',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'noemail',  // LDAP username without suffix
        firstname: 'John',
        lastname: 'Doe',
        email_address: '',
        github_suffix: 'LinkedIn',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });

    it('should handle null email', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'nullemail_Company',
        user: {
          login: 'nullemail_Company',
          id: 12345,
          name: 'Jane Smith',
          email: null,
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'nullemail',  // LDAP username without suffix
        firstname: 'Jane',
        lastname: 'Smith',
        email_address: '',
        github_suffix: 'Company',
        avatar_url: 'https://avatars.githubusercontent.com/u/12345',
      });
    });
  });

  describe('edge cases - EMU suffix parsing', () => {
    it('should parse standard EMU suffix', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'user_LinkedIn',
        user: {
          login: 'user_LinkedIn',
          id: 12345,
          name: 'Test User',
          email: 'test@linkedin.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed.github_suffix).toBe('LinkedIn');
    });

    it('should return null for hyphenated username (no underscore)', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'user-MyCompany',
        user: {
          login: 'user-MyCompany',
          id: 12345,
          name: 'Test User',
          email: 'test@company.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      // parseEmuSuffix only parses underscores, not hyphens
      expect(parsed.github_suffix).toBeNull();
    });

    it('should return null for username without suffix', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'regularuser',
        user: {
          login: 'regularuser',
          id: 12345,
          name: 'Regular User',
          email: 'regular@github.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed.github_suffix).toBeNull();
    });

    it('should parse valid suffix after underscore', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'user_name',
        user: {
          login: 'user_name',
          id: 12345,
          name: 'User Name',
          email: 'user@github.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/12345',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      // parseEmuSuffix extracts anything after last underscore that matches pattern
      // "name" matches /^[a-z0-9-]{2,20}$/i, so it's considered a valid suffix
      expect(parsed.github_suffix).toBe('name');
      expect(parsed.username).toBe('user');  // LDAP username without suffix
    });
  });

  describe('error handling - invalid result', () => {
    it('should return empty data when user is undefined', () => {
      const result: ValidateUserResult = {
        valid: false,
        error: 'User not found',
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: '',
        firstname: '',
        lastname: '',
        email_address: '',
        github_suffix: null,
        avatar_url: '',
      });
    });

    it('should handle result with valid=true but no user object', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'someuser',
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: '',
        firstname: '',
        lastname: '',
        email_address: '',
        github_suffix: null,
        avatar_url: '',
      });
    });
  });

  describe('comprehensive scenarios', () => {
    it('should handle complete user profile with all fields', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'jdoe_Acme',
        user: {
          login: 'jdoe_Acme',
          id: 98765,
          name: 'John David Doe',
          email: 'john.doe@acme.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/98765',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'jdoe',  // LDAP username without suffix
        firstname: 'John',
        lastname: 'David Doe',
        email_address: 'john.doe@acme.com',
        github_suffix: 'Acme',
        avatar_url: 'https://avatars.githubusercontent.com/u/98765',
      });
    });

    it('should handle minimal user profile (no name, no email)', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'minimal_Company',
        user: {
          login: 'minimal_Company',
          id: 11111,
          name: null,
          email: null,
          avatar_url: 'https://avatars.githubusercontent.com/u/11111',
          type: 'User',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'minimal',  // LDAP username without suffix
        firstname: '',
        lastname: '',
        email_address: '',
        github_suffix: 'Company',
        avatar_url: 'https://avatars.githubusercontent.com/u/11111',
      });
    });

    it('should handle organization accounts', () => {
      const result: ValidateUserResult = {
        valid: true,
        username: 'acme-corp',
        user: {
          login: 'acme-corp',
          id: 55555,
          name: 'Acme Corporation',
          email: 'contact@acme.com',
          avatar_url: 'https://avatars.githubusercontent.com/u/55555',
          type: 'Organization',
        },
      };

      const parsed = parseGitHubUser(result);

      expect(parsed).toEqual({
        username: 'acme-corp',
        firstname: 'Acme',
        lastname: 'Corporation',
        email_address: 'contact@acme.com',
        github_suffix: null,
        avatar_url: 'https://avatars.githubusercontent.com/u/55555',
      });
    });
  });
});
