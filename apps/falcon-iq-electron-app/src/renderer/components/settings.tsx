import { useRouter } from "@tanstack/react-router";
import { useEffect, useState, useCallback } from "react";
import { Modal } from "@libs/shared/ui/modal/modal";
import { useForm } from "react-hook-form";
import { validateGitHubToken, validateGitHubUser, type ValidateTokenResult, type ValidateUserResult, githubUsername } from "@libs/integrations/github";
import { Loader2, Plus, Trash2 } from "lucide-react";
import { useAsyncValidation } from '@libs/shared/hooks/use-async-validation';

interface SettingsFormData {
  pat: string;
}

export const Settings = () => {
  const router = useRouter();
  const [users, setUsers] = useState<string[]>([]);
  const [newUser, setNewUser] = useState('');
  const [tokenMetadata, setTokenMetadata] = useState<ValidateTokenResult | null>(null);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);

  const { register, handleSubmit, setValue, getValues } = useForm<SettingsFormData>({
    defaultValues: { pat: "" },
    mode: "onBlur", // Validate on blur instead of only on submit
  });

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
  } = useAsyncValidation({
    validator: (username: string) => {
      const currentPat = getValues("pat");
      return validateGitHubUser(currentPat, username);
    },
    extractErrorMessage: (result: ValidateUserResult) => result.error ?? "Invalid GitHub username",
    fallbackErrorMessage: "Failed to validate username. Please try again."
  });

  useEffect(() => {
    const storedPat = localStorage.getItem("manager_buddy_pat") ?? "";
    const storedUsers = localStorage.getItem("manager_buddy_users");

    setValue("pat", storedPat);

    // Validate the stored PAT to get metadata
    if (storedPat) {
      void validate(storedPat);
    }

    if (storedUsers) {
      try {
        const parsedUsers = JSON.parse(storedUsers) as string[];
        setUsers(parsedUsers);
      } catch {
        // If parsing fails, start with empty array
        setUsers([]);
      }
    }
  }, [setValue]); // Only setValue is needed - validate is intentionally omitted to run only on mount

  const handleClose = useCallback(() => {
    router.history.back();
  }, [router]);

  const handleAddUser = useCallback(() => {
    const trimmedUser = newUser.trim();
    const isDuplicate = users.some(user => user.toLowerCase() === trimmedUser.toLowerCase());

    if (isDuplicate && trimmedUser) {
      setDuplicateError(`"${trimmedUser}" has already been added`);
      return;
    }

    if (trimmedUser && isUsernameValid && !isValidatingUsername) {
      setUsers([...users, trimmedUser]);
      setNewUser('');
      setDuplicateError(null);
      resetUsernameValidation(); // Clear validation state for next user
    }
  }, [newUser, users, isUsernameValid, isValidatingUsername, resetUsernameValidation]);

  const handleRemoveUser = useCallback((userToRemove: string) => {
    setUsers(users.filter((user) => user !== userToRemove));
  }, [users]);

  const onSubmit = (data: SettingsFormData) => {
    localStorage.setItem("manager_buddy_pat", data.pat);
    localStorage.setItem("manager_buddy_users", JSON.stringify(users));
    handleClose();
  };

  const patField = register("pat");

  return (
    <Modal
      isOpen={true}
      onClose={handleClose}
      title="Settings"
      size="xl"
      initialFocusId="pat"
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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
                }}
                onBlur={(e) => {
                  const username = githubUsername(e.target.value, tokenMetadata?.emu_suffix || '');
                  if (username !== e.target.value) {
                    setNewUser(username);
                  }
                  void validateUsername(username);
                }}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddUser())}
                placeholder="Enter username"
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
              onClick={handleAddUser}
              disabled={!isUsernameValid || isValidatingUsername || !newUser.trim()}
              className="rounded-lg bg-primary px-3 py-2 text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Add user"
            >
              <Plus className="h-5 w-5" />
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
            {users.map((user) => (
              <div
                key={user}
                className="flex items-center justify-between rounded-lg border border-border bg-background px-3 py-2"
              >
                <span className="text-sm text-foreground">{user}</span>
                <button
                  type="button"
                  onClick={() => handleRemoveUser(user)}
                  className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-destructive"
                  aria-label={`Remove ${user}`}
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
            disabled={!isValid || isValidating}
            className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Save
          </button>
        </div>
      </form>
    </Modal>
  );
};
