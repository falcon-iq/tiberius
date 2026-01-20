import { useState, useCallback } from 'react';
import { Modal } from '@libs/shared/ui/modal/modal';
import { Plus, Trash2, Sun, Moon, Loader2 } from 'lucide-react';
import { validateGitHubToken, validateGitHubUser, type ValidateTokenResult, type ValidateUserResult } from '@libs/integrations/github/auth';
import { githubUsername } from '@libs/integrations/github/username';
import { useAsyncValidation } from '@libs/shared/hooks/use-async-validation';
import { useTheme } from '@libs/shared/hooks/use-theme';
import { useForm } from 'react-hook-form';


interface OnboardingWizardProps {
  isOpen: boolean;
  onComplete: (pat: string, users: string[]) => void;
}

interface Step1FormData {
  pat: string;
}

export const OnboardingWizard = ({ isOpen, onComplete }: OnboardingWizardProps) => {
  const [step, setStep] = useState(1);
  const [users, setUsers] = useState<string[]>([]);
  const [newUser, setNewUser] = useState('');
  const [tokenMetadata, setTokenMetadata] = useState<ValidateTokenResult | null>(null);
  const [duplicateError, setDuplicateError] = useState<string | null>(null);

  // Use shared theme hook instead of managing theme locally
  const { isDarkMode, toggleTheme } = useTheme();

  // React Hook Form for Step 1 (PAT only, suffix is auto-detected)
  const { register, watch } = useForm<Step1FormData>({
    defaultValues: { pat: "" },
    mode: "onBlur", // Validate on blur
  });

  const pat = watch("pat");

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
    validator: (username: string) => validateGitHubUser(pat, username),
    extractErrorMessage: (result: ValidateUserResult) => result.error ?? "Invalid GitHub username",
    fallbackErrorMessage: "Failed to validate username. Please try again."
  });

  const handleAddUser = useCallback(() => {
    const trimmedUser = newUser.trim();

    if (trimmedUser && isUsernameValid && !isValidatingUsername) {
      setUsers(prev => {
        // Check for duplicates using the current state
        const isDuplicate = prev.some(user => user.toLowerCase() === trimmedUser.toLowerCase());

        if (isDuplicate) {
          setDuplicateError(`"${trimmedUser}" has already been added`);
          return prev; // Return unchanged state
        }

        // Clear error and add new user
        setDuplicateError(null);
        return [...prev, trimmedUser];
      });
      setNewUser('');
      resetUsernameValidation(); // Clear validation state for next user
    }
  }, [newUser, isUsernameValid, isValidatingUsername, resetUsernameValidation]);

  const handleRemoveUser = useCallback((userToRemove: string) => {
    setUsers(prev => prev.filter((user) => user !== userToRemove));
  }, []);

  const handleNext = useCallback(() => {
    if (step === 1 && isValid && !isValidating) {
      setStep(2);
    }
  }, [step, isValid, isValidating]);

  const handleComplete = useCallback(() => {
    if (users.length > 0) {
      onComplete(pat, users);
      // Reset state after completion
      setStep(1);
      setUsers([]);
      setNewUser('');
    }
  }, [users, pat, onComplete]);

  const handleClose = useCallback(() => {
    // Onboarding wizard cannot be dismissed - user must complete setup
  }, []);

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      size="xl"
      closeOnBackdrop={false}
      closeOnEscape={false}
      showCloseButton={false}
    >
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center relative">
          <h1 className="text-2xl font-bold text-foreground">Welcome to Falcon IQ</h1>
          <p className="mt-2 text-sm text-muted-foreground">Let's get you set up in just a few steps</p>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="absolute top-0 right-0 rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            type="button"
          >
            {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center gap-2">
          <div className={`h-2 w-24 rounded-full transition-colors ${step >= 1 ? 'bg-primary' : 'bg-muted'}`} />
          <div className={`h-2 w-24 rounded-full transition-colors ${step >= 2 ? 'bg-primary' : 'bg-muted'}`} />
        </div>

        {/* Step 1: PAT Token */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="mb-4 text-lg font-semibold text-foreground">Step 1: Add Your Personal Access Token</h2>

              {/* PAT Field */}
              <div className="mb-4">
                <label htmlFor="wizard-pat" className="mb-2 block text-sm font-medium text-foreground">
                  Personal Access Token
                </label>

                <div className="relative">
                  <input
                    id="wizard-pat"
                    type="password"
                    {...register("pat")}
                    onBlur={(e) => {
                      void validate(e.target.value);
                    }}
                    onKeyDown={(e) => e.key === 'Enter' && handleNext()}
                    placeholder="Enter your PAT"
                    className={`w-full rounded-lg border bg-background px-4 py-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${validationError
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

                <div className="mt-2 min-h-[20px]">
                  {validationError ? (
                    <p className="text-xs text-destructive">
                      {validationError}
                    </p>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      This token will be used to authenticate with your project management tools.
                    </p>
                  )}
                </div>
              </div>

              {/* EMU Status Display */}
              {isValid && tokenMetadata && (
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-foreground">
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

            <div className="flex justify-end">
              <button
                onClick={handleNext}
                disabled={!isValid || isValidating}
                className="rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
              >
                Next
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Add Users */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="mb-4 text-lg font-semibold text-foreground">Step 2: Add Team Members</h2>
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
                        const username = githubUsername(e.target.value, tokenMetadata?.emu_suffix || '');
                        if (username !== e.target.value) {
                          setNewUser(username);
                        }
                        void validateUsername(username);
                      }}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddUser()}
                      placeholder="Enter username"
                      className={`w-full rounded-lg border bg-background px-4 py-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${usernameValidationError || duplicateError
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
                    <p className="text-xs text-destructive">
                      {duplicateError}
                    </p>
                  ) : usernameValidationError ? (
                    <p className="text-xs text-destructive">
                      {usernameValidationError}
                    </p>
                  ) : null}
                </div>
              </div>

              {/* User List */}
              <div className="space-y-2">
                {users.length === 0 && (
                  <p className="py-8 text-center text-sm text-muted-foreground">No team members added yet</p>
                )}
                {users.map((user, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg border border-border bg-background px-4 py-3"
                  >
                    <span className="text-sm text-foreground">{user}</span>
                    <button
                      onClick={() => handleRemoveUser(user)}
                      className="rounded p-1 text-muted-foreground transition-colors hover:bg-accent hover:text-destructive"
                      type="button"
                      aria-label={`Remove ${user}`}
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="rounded-lg border border-border bg-background px-6 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent"
                type="button"
              >
                Back
              </button>
              <button
                onClick={handleComplete}
                disabled={users.length === 0}
                className="rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
                type="button"
              >
                Complete Setup
              </button>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};
