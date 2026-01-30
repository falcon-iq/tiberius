import { useRouter } from "@tanstack/react-router";
import { useEffect, useState, useCallback } from "react";
import { Modal } from "@libs/shared/ui/modal";
import { useForm } from "react-hook-form";
import { validateGitHubToken, validateGitHubUser, type ValidateTokenResult, type ValidateUserResult, githubUsername, parseGitHubUser } from "@libs/integrations/github";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { useAsyncValidation } from '@libs/shared/hooks/use-async-validation';
import { useUsers, useAddUser, useDeleteUser } from '@hooks/use-users';
import { useSettings, useUpdateSettings } from '@hooks/use-settings';
import { stripEmuSuffix } from '@libs/shared/utils/user-display';

interface SettingsFormData {
  firstName: string;
  lastName: string;
  ldapUsername: string;
  pat: string;
}

interface TeamMember {
  username: string;
  firstname?: string;
  lastname?: string;
  email_address?: string;
  github_suffix?: string | null;
  avatar_url?: string;
}

export const Settings = () => {
  const router = useRouter();
  const [users, setUsers] = useState<TeamMember[]>([]);
  const [newUser, setNewUser] = useState('');
  const [tokenMetadata, setTokenMetadata] = useState<ValidateTokenResult | null>(null);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);
  const [usernameValidationResult, setUsernameValidationResult] = useState<ValidateUserResult | null>(null);

  const { register, handleSubmit, setValue, getValues, formState: { errors, isValid: isFormValid } } = useForm<SettingsFormData>({
    defaultValues: {
      firstName: "",
      lastName: "",
      ldapUsername: "",
      pat: "",
    },
    mode: "onBlur",
  });

  // TanStack Query hooks for database and settings operations
  const { data: settings } = useSettings();
  const { data: existingUsers, isLoading: isLoadingUsers } = useUsers();
  const addUserMutation = useAddUser();
  const deleteUserMutation = useDeleteUser();
  const updateSettingsMutation = useUpdateSettings();

  // Use the async validation hook for PAT
  const { validate, isValidating, validationError, isValid } = useAsyncValidation({
    validator: validateGitHubToken,
    extractErrorMessage: (result: ValidateTokenResult) => result.error ?? "Invalid GitHub token",
    fallbackErrorMessage: "Failed to validate token. Please check your connection.",
    onSuccess: (result: ValidateTokenResult) => {
      setTokenMetadata(result);
    },
    onError: () => {
      setTokenMetadata(null);
    }
  });

  // Use the async validation hook for GitHub username
  const {
    validate: validateUsername,
    isValidating: isValidatingUsername,
    validationError: usernameValidationError,
    isValid: isUsernameValid,
    reset: resetUsernameValidation
  } = useAsyncValidation<ValidateUserResult>({
    validator: (username: string) => {
      const currentPat = getValues("pat");
      return validateGitHubUser(currentPat, username);
    },
    extractErrorMessage: (result: ValidateUserResult) => result.error ?? "Invalid GitHub username",
    fallbackErrorMessage: "Failed to validate username. Please try again.",
    onSuccess: (result: ValidateUserResult) => {
      setUsernameValidationResult(result);
    },
    onError: () => {
      setUsernameValidationResult(null);
    }
  });

  // Load settings from settings.json on mount
  useEffect(() => {
    if (settings) {
      // Load user profile
      setValue("firstName", settings.user.firstName || "");
      setValue("lastName", settings.user.lastName || "");
      setValue("ldapUsername", settings.user.ldapUsername || "");

      // Load GitHub PAT
      const storedPat = settings.integrations.github.pat || "";
      setValue("pat", storedPat);

      // Validate the stored PAT to get metadata
      if (storedPat) {
        void validate(storedPat);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- validate function identity changes every render, but we only want to run this on settings/setValue change
  }, [settings, setValue]);

  // Hydrate users from database
  useEffect(() => {
    if (existingUsers && existingUsers.length > 0) {
      const teamMembers: TeamMember[] = existingUsers.map(u => ({
        username: u.username,
        firstname: u.firstname || undefined,
        lastname: u.lastname || undefined,
        email_address: u.email_address || undefined,
        github_suffix: u.github_suffix || undefined,
      }));
      setUsers(teamMembers);
    }
  }, [existingUsers]);

  const handleClose = useCallback(() => {
    router.history.back();
  }, [router]);

  const handleAddUser = useCallback(async () => {
    const trimmedUser = newUser.trim();

    if (!trimmedUser || !isUsernameValid || isValidatingUsername || !usernameValidationResult) {
      return;
    }

    // Parse GitHub user data (includes firstname, lastname, email, etc.)
    const parsedUser = parseGitHubUser(usernameValidationResult);

    // Check for duplicates in current state and database
    const isDuplicate = users.some(user => user.username.toLowerCase() === parsedUser.username.toLowerCase());

    if (isDuplicate) {
      setDuplicateError(`"${parsedUser.username}" has already been added`);
      return;
    }

    try {
      // Save to database immediately with full user data
      await addUserMutation.mutateAsync({
        username: parsedUser.username,
        github_suffix: parsedUser.github_suffix || null,
        firstname: parsedUser.firstname || null,
        lastname: parsedUser.lastname || null,
        email_address: parsedUser.email_address || null,
        avatar_url: parsedUser.avatar_url || null,
      });

      // Update local state with parsed user object
      setUsers([...users, parsedUser]);
      setNewUser('');
      setDuplicateError(null);
      setUsernameValidationResult(null);
      resetUsernameValidation();
    } catch (error) {
      console.error('Failed to add user:', error);
      // Check if it's a duplicate error from database
      if ((error as Error).message.includes('already exists')) {
        setDuplicateError(`"${parsedUser.username}" already exists in database`);
      }
    }
  }, [newUser, users, isUsernameValid, isValidatingUsername, usernameValidationResult, addUserMutation, resetUsernameValidation]);

  const handleRemoveUser = useCallback(async (userToRemove: string) => {
    // Remove from local state
    setUsers(users.filter((user) => user.username !== userToRemove));

    // Find user in database and delete
    const existingUser = existingUsers?.find(u => u.username === userToRemove);
    if (existingUser) {
      try {
        await deleteUserMutation.mutateAsync(existingUser.id);
      } catch (error) {
        console.error('Failed to delete user from database:', error);
        // TODO: Show error notification
      }
    }
  }, [users, existingUsers, deleteUserMutation]);

  const onSubmit = async (data: SettingsFormData) => {
    try {
      // Save user profile and PAT to settings.json
      await updateSettingsMutation.mutateAsync({
        user: {
          firstName: data.firstName,
          lastName: data.lastName,
          ldapUsername: data.ldapUsername,
        },
        integrations: {
          github: {
            pat: data.pat,
            emuSuffix: tokenMetadata?.emu_suffix,
            username: tokenMetadata?.username,
          },
        },
      });
      // Users are already saved to SQLite database (no need to save here)
      handleClose();
    } catch (error) {
      console.error('Failed to save settings:', error);
      // TODO: Show error notification to user
    }
  };

  const patField = register("pat");

  return (
    <Modal
      isOpen={true}
      onClose={handleClose}
      title="Settings"
      size="xl"
      initialFocusId="firstName"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* User Profile Section */}
        <div>
          <h3 className="mb-3 text-base font-semibold text-foreground">
            User Profile
          </h3>

          {/* First Name */}
          <div className="mb-4">
            <label
              htmlFor="firstName"
              className="mb-2 block text-sm font-medium text-foreground"
            >
              First Name
            </label>
            <input
              id="firstName"
              type="text"
              {...register("firstName", { required: "First name is required" })}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
            {errors.firstName && (
              <p className="mt-1 text-xs text-destructive">
                {errors.firstName.message}
              </p>
            )}
          </div>

          {/* Last Name */}
          <div className="mb-4">
            <label
              htmlFor="lastName"
              className="mb-2 block text-sm font-medium text-foreground"
            >
              Last Name
            </label>
            <input
              id="lastName"
              type="text"
              {...register("lastName", { required: "Last name is required" })}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            />
            {errors.lastName && (
              <p className="mt-1 text-xs text-destructive">
                {errors.lastName.message}
              </p>
            )}
          </div>

          {/* LDAP Username (read-only) */}
          <div className="mb-4">
            <label
              htmlFor="ldapUsername"
              className="mb-2 block text-sm font-medium text-foreground"
            >
              LDAP Username
            </label>
            <input
              id="ldapUsername"
              type="text"
              {...register("ldapUsername")}
              readOnly
              disabled
              className="w-full rounded-lg border border-border bg-muted px-3 py-2 text-sm text-muted-foreground cursor-not-allowed"
            />
            <p className="mt-1 text-xs text-muted-foreground">
              LDAP username cannot be changed after setup
            </p>
          </div>
        </div>

        {/* Divider */}
        <div className="my-6 border-t border-border" />

        {/* GitHub Integration Section */}
        <div>
          <h3 className="mb-3 text-base font-semibold text-foreground">
            GitHub Integration
          </h3>

          {/* Personal Access Token */}
          <div>
          <label
            htmlFor="pat"
            className="mb-2 block text-sm font-medium text-foreground"
          >
            Personal Access Token
          </label>

          <div className="relative">
            <input
              id="pat"
              type="password"
              {...patField}
              onBlur={(e) => {
                patField.onBlur(e);
                void validate(e.target.value);
              }}
              placeholder="•••"
              className={`w-full rounded-lg border bg-background px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${validationError
                ? "border-destructive focus:ring-destructive"
                : "border-border focus:ring-primary"
                }`}
            />

            {isValidating && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            )}
          </div>

          <div className="mt-1 min-h-[16px]">
            {validationError ? (
              <p className="text-xs text-destructive">
                {validationError}
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">
                Your PAT will be stored securely and used to authenticate with your project management tools.
              </p>
            )}
          </div>
        </div>

          {/* EMU Status Display */}
          {isValid && tokenMetadata && (
            <div>
              <label className="mb-2 block text-sm font-medium text-foreground">
                Enterprise Managed User (EMU) Status
              </label>
              <div className={`px-4 py-3 rounded-lg border ${tokenMetadata.emu
                ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                : 'bg-muted border-border'
                }`}>
                {tokenMetadata.emu && tokenMetadata.emu_suffix ? (
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                      ✓ EMU User Detected
                    </p>
                    <p className="text-sm text-foreground">
                      Company Suffix: <span className="font-mono font-semibold">{tokenMetadata.emu_suffix}</span>
                    </p>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Not an EMU user
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="my-6 border-t border-border" />

        {/* Team Members */}
        <div>
          <label
            htmlFor="new-user"
            className="mb-2 block text-sm font-medium text-foreground"
          >
            Team Members
          </label>

          <div className="relative flex gap-2">
            <div className="relative flex-1">
              <input
                id="new-user"
                type="text"
                value={newUser}
                onChange={(e) => {
                  setNewUser(e.target.value);
                  setDuplicateError(null);
                  setUsernameValidationResult(null);
                }}
                onBlur={(e) => {
                  const ldapUsername = e.target.value.trim();
                  // Build GitHub username for validation (with suffix if EMU user)
                  const githubUsernameForValidation = tokenMetadata?.emu_suffix
                    ? githubUsername(ldapUsername, tokenMetadata.emu_suffix)
                    : ldapUsername;
                  // Don't update the input field - keep showing just LDAP username
                  void validateUsername(githubUsernameForValidation);
                }}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddUser())}
                placeholder="Enter LDAP username"
                className={`w-full rounded-lg border bg-background px-3 py-2 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${usernameValidationError || duplicateError
                  ? "border-destructive focus:ring-destructive"
                  : "border-border focus:ring-primary"
                  }`}
              />

              {isValidatingUsername && (
                <div className="absolute right-3 top-1/2 -translate-y-1/2">
                  <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={() => void handleAddUser()}
              disabled={!isUsernameValid || isValidatingUsername || !newUser.trim() || addUserMutation.isPending}
              className="rounded-lg bg-primary px-3 py-2 text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Add user"
            >
              {addUserMutation.isPending ? (
                <Loader2 className="h-5 w-5 animate-spin" />
              ) : (
                <Plus className="h-5 w-5" />
              )}
            </button>
          </div>

          <div className="mt-1 min-h-[16px]">
            {duplicateError ? (
              <p className="text-xs text-destructive">
                {duplicateError}
              </p>
            ) : usernameValidationError ? (
              <p className="text-xs text-destructive">
                {usernameValidationError}
              </p>
            ) : null}
          </div>

          {/* User List */}
          <div className="mt-3 space-y-2 max-h-[200px] overflow-y-auto">
            {isLoadingUsers && (
              <div className="py-4 flex justify-center">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            )}
            {!isLoadingUsers && users.length === 0 && (
              <p className="py-4 text-center text-xs text-muted-foreground">No team members added yet</p>
            )}
            {!isLoadingUsers && users.map((user) => (
              <div
                key={user.username}
                className="flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2"
              >
                <div className="flex-1">
                  <span className="text-sm font-medium text-foreground">{stripEmuSuffix(user.username, user.github_suffix)}</span>
                  {user.firstname && user.lastname && (
                    <span className="ml-2 text-xs text-muted-foreground">
                      ({user.firstname} {user.lastname})
                    </span>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => void handleRemoveUser(user.username)}
                  className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-destructive"
                  aria-label={`Remove ${user.username}`}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={handleClose}
            className="flex-1 rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={!isFormValid || !isValid || isValidating}
            className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Done
          </button>
        </div>
      </form>
    </Modal>
  );
};
