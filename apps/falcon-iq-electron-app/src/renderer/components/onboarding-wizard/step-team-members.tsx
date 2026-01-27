/**
 * Step 3: Team Members
 */

import { useState, useCallback, useEffect } from 'react';
import { Plus, Trash2, Loader2 } from 'lucide-react';
import { validateGitHubUser, githubUsername, parseGitHubUser, parseEmuSuffix, type ValidateUserResult } from '@libs/integrations/github';
import { useAsyncValidation } from '@libs/shared/hooks/use-async-validation';
import { useUsers, useAddUser, useDeleteUser } from '@hooks/use-users';
import { useUpdateSettings } from '@hooks/use-settings';
import type { Step3Props, TeamMember } from './types';

/**
 * Strip EMU suffix from username for display purposes
 * @param username - Full GitHub username (e.g., "bsteyn_LinkedIn")
 * @returns LDAP username without suffix (e.g., "bsteyn")
 */
const getDisplayUsername = (username: string): string => {
  const suffix = parseEmuSuffix(username);
  if (suffix) {
    return username.slice(0, username.lastIndexOf('_'));
  }
  return username;
};

export const StepTeamMembers = ({ userDetails, githubIntegration, onBack, onComplete }: Step3Props) => {
  const [users, setUsers] = useState<TeamMember[]>([]);
  const [newUser, setNewUser] = useState('');
  const [duplicateError, setDuplicateError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  const { data: existingUsers, isLoading: isLoadingUsers } = useUsers();
  const addUserMutation = useAddUser();
  const deleteUserMutation = useDeleteUser();
  const updateSettingsMutation = useUpdateSettings();

  // Hydrate existing users from database
  useEffect(() => {
    if (existingUsers && existingUsers.length > 0) {
      const existingTeamMembers: TeamMember[] = existingUsers.map((u) => ({
        username: u.username,
        firstname: u.firstname || undefined,
        lastname: u.lastname || undefined,
        email_address: u.email_address || undefined,
        github_suffix: u.github_suffix || undefined,
      }));
      setUsers((prev) => {
        const existingUsernames = new Set(prev.map(u => u.username.toLowerCase()));
        const newMembers = existingTeamMembers.filter(
          member => !existingUsernames.has(member.username.toLowerCase())
        );
        return [...prev, ...newMembers];
      });
    }
  }, [existingUsers]);

  const [validationResult, setValidationResult] = useState<ValidateUserResult | null>(null);

  // Use the async validation hook for GitHub username
  const {
    validate: validateUsername,
    isValidating: isValidatingUsername,
    validationError: usernameValidationError,
    isValid: isUsernameValid,
    reset: resetUsernameValidation,
  } = useAsyncValidation<ValidateUserResult>({
    validator: (username: string) => validateGitHubUser(githubIntegration.pat, username),
    extractErrorMessage: (result: ValidateUserResult) =>
      result.error ?? 'Invalid GitHub username',
    fallbackErrorMessage: 'Failed to validate username. Please try again.',
    onSuccess: (result: ValidateUserResult) => {
      setValidationResult(result);
    },
    onError: () => {
      setValidationResult(null);
    },
  });

  const handleAddUser = useCallback(() => {
    const trimmedUser = newUser.trim();

    if (trimmedUser && isUsernameValid && !isValidatingUsername && validationResult) {
      // Parse GitHub user data
      const parsedUser = parseGitHubUser(validationResult);

      setUsers((prev) => {
        const isDuplicate = prev.some(
          (user) => user.username.toLowerCase() === parsedUser.username.toLowerCase()
        );

        if (isDuplicate) {
          setDuplicateError(`"${parsedUser.username}" has already been added`);
          return prev;
        }

        setDuplicateError(null);
        return [...prev, parsedUser];
      });
      setNewUser('');
      resetUsernameValidation();
    }
  }, [newUser, isUsernameValid, isValidatingUsername, validationResult, resetUsernameValidation]);

  const handleRemoveUser = useCallback(
    async (usernameToRemove: string) => {
      setUsers((prev) => prev.filter((user) => user.username !== usernameToRemove));

      const existingUser = existingUsers?.find((u) => u.username === usernameToRemove);
      if (existingUser) {
        try {
          await deleteUserMutation.mutateAsync(existingUser.id);
        } catch (error) {
          console.error('Failed to delete user from database:', error);
        }
      }
    },
    [existingUsers, deleteUserMutation]
  );

  const handleComplete = useCallback(async () => {
    if (users.length === 0) return;

    setIsSaving(true);

    try {
      // 1. Add current user to team members if not already present
      // Only append EMU suffix if present (non-EMU users use raw LDAP username)
      const currentUserGitHubUsername = githubIntegration.emuSuffix
        ? githubUsername(userDetails.ldapUsername, githubIntegration.emuSuffix)
        : userDetails.ldapUsername;

      const currentUserExists = users.some(
        (u) => u.username.toLowerCase() === currentUserGitHubUsername.toLowerCase()
      );

      let allUsers = users;

      if (!currentUserExists) {
        // Fetch current user's GitHub profile
        const currentUserResult = await validateGitHubUser(
          githubIntegration.pat,
          currentUserGitHubUsername
        );

        if (currentUserResult.valid && currentUserResult.user) {
          const parsedCurrentUser = parseGitHubUser(currentUserResult);
          // Create new array instead of mutating state
          allUsers = [...users, parsedCurrentUser];
        }
      }

      // 2. Save all new users to database with GitHub profile data
      const existingUsernames = existingUsers?.map((u) => u.username.toLowerCase()) || [];

      const newUsers = allUsers.filter(
        (user) => !existingUsernames.includes(user.username.toLowerCase())
      );

      for (const user of newUsers) {
        await addUserMutation.mutateAsync({
          username: user.username,
          github_suffix: user.github_suffix || null,
          email_address: user.email_address || null,
          firstname: user.firstname || null,
          lastname: user.lastname || null,
        });
      }

      // 3. Set onboardingCompleted to true
      await updateSettingsMutation.mutateAsync({
        onboardingCompleted: true,
      });

      onComplete();
    } catch (error) {
      console.error('Failed to save users:', error);
    } finally {
      setIsSaving(false);
    }
  }, [users, userDetails, existingUsers, githubIntegration, addUserMutation, updateSettingsMutation, onComplete]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          Step 3: Add Team Members
        </h2>
        <div className="mb-4">
          <div className="relative flex gap-2">
            <div className="relative flex-1">
              <input
                id="wizard-new-user"
                type="text"
                value={newUser}
                onChange={(e) => {
                  setNewUser(e.target.value);
                  setDuplicateError(null);
                }}
                onBlur={(e) => {
                  const ldapUsername = e.target.value.trim();
                  // Build GitHub username for validation (with suffix if EMU user)
                  const githubUsernameForValidation = githubIntegration.emuSuffix
                    ? githubUsername(ldapUsername, githubIntegration.emuSuffix)
                    : ldapUsername;
                  // Don't update the input field - keep showing just LDAP username
                  void validateUsername(githubUsernameForValidation);
                }}
                onKeyDown={(e) => e.key === 'Enter' && handleAddUser()}
                placeholder="Enter LDAP username"
                className={`w-full rounded-lg border bg-background px-4 py-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${
                  usernameValidationError || duplicateError
                    ? 'border-destructive focus:ring-destructive'
                    : 'border-border focus:ring-primary'
                }`}
              />

              {isValidatingUsername && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              )}
            </div>

            <button
              onClick={handleAddUser}
              disabled={!isUsernameValid || isValidatingUsername || !newUser.trim()}
              className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              type="button"
              aria-label="Add user"
            >
              <Plus className="h-5 w-5" />
            </button>
          </div>

          <div className="mt-2 min-h-[20px]">
            {duplicateError ? (
              <p className="text-xs text-destructive">{duplicateError}</p>
            ) : usernameValidationError ? (
              <p className="text-xs text-destructive">{usernameValidationError}</p>
            ) : null}
          </div>
        </div>

        {/* User List */}
        <div className="space-y-2">
          {isLoadingUsers && (
            <div className="flex justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}
          {!isLoadingUsers && users.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No team members added yet
            </p>
          )}
          {!isLoadingUsers &&
            users.map((user) => (
              <div
                key={user.username}
                className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3"
              >
                <div className="flex-1">
                  <span className="text-sm font-medium text-foreground">{getDisplayUsername(user.username)}</span>
                  {user.firstname && user.lastname && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      ({user.firstname} {user.lastname})
                    </span>
                  )}
                </div>
                <button
                  onClick={() => void handleRemoveUser(user.username)}
                  className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-destructive"
                  type="button"
                  aria-label={`Remove ${user.username}`}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
        </div>
      </div>

      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="rounded-lg border border-border bg-background px-6 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          type="button"
        >
          Back
        </button>
        <button
          onClick={() => void handleComplete()}
          disabled={users.length === 0 || isSaving}
          className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          type="button"
        >
          {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
          {isSaving ? 'Saving...' : 'Complete Setup'}
        </button>
      </div>
    </div>
  );
};
