import { useState, useCallback, useEffect } from 'react';
import { Modal } from '@libs/shared/ui/modal/modal';
import { Plus, Trash2, Sun, Moon, Loader2 } from 'lucide-react';
import { validateGitHubToken, validateGitHubUser, type ValidateTokenResult, type ValidateUserResult } from '@libs/integrations/github/auth';
import { githubUsername } from '@libs/integrations/github/username';
import { useAsyncValidation } from '@libs/shared/hooks/use-async-validation';
import { useForm } from 'react-hook-form';


interface OnboardingWizardProps {
  isOpen: boolean;
  onComplete: (pat: string, users: string[]) => void;
}

interface Step1FormData {
  pat: string;
  suffix: string;
}

export const OnboardingWizard = ({ isOpen, onComplete }: OnboardingWizardProps) => {
  const [step, setStep] = useState(1);
  const [users, setUsers] = useState<string[]>([]);
  const [newUser, setNewUser] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);

  // React Hook Form for Step 1 (PAT + Suffix)
  const { register, watch, formState: { errors } } = useForm<Step1FormData>({
    defaultValues: { pat: "", suffix: "" },
    mode: "onBlur", // Validate on blur
  });

  const pat = watch("pat");
  const suffix = watch("suffix");

  // Use the async validation hook for PAT
  const { validate, isValidating, validationError, isValid } = useAsyncValidation({
    validator: validateGitHubToken,
    extractErrorMessage: (result: ValidateTokenResult) => result.error ?? "Invalid GitHub token",
    fallbackErrorMessage: "Failed to validate token. Please check your connection."
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

  // Initialize theme from system preference or localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const shouldBeDark = savedTheme === 'dark' || (!savedTheme && prefersDark);

    setIsDarkMode(shouldBeDark);
    if (shouldBeDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setIsDarkMode((prev) => {
      const newIsDark = !prev;
      if (newIsDark) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
      }
      return newIsDark;
    });
  }, []);

  const handleAddUser = useCallback(() => {
    if (newUser.trim() && !users.includes(newUser.trim()) && isUsernameValid && !isValidatingUsername) {
      setUsers([...users, newUser.trim()]);
      setNewUser('');
      resetUsernameValidation(); // Clear validation state for next user
    }
  }, [newUser, users, isUsernameValid, isValidatingUsername, resetUsernameValidation]);

  const handleRemoveUser = useCallback((userToRemove: string) => {
    setUsers(users.filter((user) => user !== userToRemove));
  }, [users]);

  const handleNext = useCallback(() => {
    if (step === 1 && isValid && !isValidating && suffix.trim().length > 0) {
      setStep(2);
    }
  }, [step, isValid, isValidating, suffix]);

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

              {/* Suffix Field */}
              <div>
                <label htmlFor="wizard-suffix" className="mb-2 block text-sm font-medium text-foreground">
                  Suffix
                </label>

                <input
                  id="wizard-suffix"
                  type="text"
                  {...register("suffix", {
                    required: "Suffix is required",
                    validate: (value) => value.trim().length > 0 || "Suffix cannot be empty"
                  })}
                  onKeyDown={(e) => e.key === 'Enter' && handleNext()}
                  placeholder="Enter suffix"
                  className={`w-full rounded-lg border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${errors.suffix
                    ? "border-destructive focus:ring-destructive"
                    : "border-border focus:ring-primary"
                    }`}
                />

                <div className="mt-2 min-h-[20px]">
                  {errors.suffix ? (
                    <p className="text-xs text-destructive">
                      {errors.suffix.message}
                    </p>
                  ) : null}
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleNext}
                disabled={!isValid || isValidating || !!errors.suffix || suffix.trim().length === 0}
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
                      onChange={(e) => setNewUser(e.target.value)}
                      onBlur={(e) => {
                        const username = githubUsername(e.target.value, suffix);
                        if (username !== e.target.value) {
                          setNewUser(username);
                        }
                        void validateUsername(username);
                      }}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddUser()}
                      placeholder="Enter username"
                      className={`w-full rounded-lg border bg-background px-4 py-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${usernameValidationError
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
                  {usernameValidationError ? (
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
                {users.map((user) => (
                  <div
                    key={user}
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
