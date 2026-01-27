/**
 * Step 2: GitHub Integration (Personal Access Token)
 */

import { useCallback, useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { Loader2 } from 'lucide-react';
import { validateGitHubToken, type ValidateTokenResult } from '@libs/integrations/github';
import { useAsyncValidation } from '@libs/shared/hooks/use-async-validation';
import { useSaveSettings } from '@hooks/use-settings';
import type { Step2Props, GitHubIntegration } from './types';

interface FormData {
  pat: string;
}

export const StepIntegrations = ({ userDetails, githubIntegration, onNext, onBack, onDataChange }: Step2Props) => {
  const { register, watch } = useForm<FormData>({
    defaultValues: { pat: githubIntegration.pat },
    mode: 'onBlur',
  });

  const pat = watch('pat');
  const saveSettingsMutation = useSaveSettings();
  const [validationResult, setValidationResult] = useState<ValidateTokenResult | null>(null);

  const { validate, isValidating, validationError, isValid } = useAsyncValidation<ValidateTokenResult>({
    validator: validateGitHubToken,
    extractErrorMessage: (result: ValidateTokenResult) =>
      result.error ?? 'Invalid GitHub token',
    fallbackErrorMessage: 'Failed to validate token. Please check your connection.',
    onSuccess: (result: ValidateTokenResult) => {
      setValidationResult(result);
    },
    onError: () => {
      setValidationResult(null);
    },
  });

  // Validate pre-filled PAT on mount (when navigating back)
  useEffect(() => {
    if (githubIntegration.pat) {
      void validate(githubIntegration.pat);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- only validate on mount
  }, []);

  // Update parent state when validation succeeds
  useEffect(() => {
    if (isValid && validationResult) {
      const integration: GitHubIntegration = {
        pat,
        emuSuffix: validationResult.emu_suffix,
        username: validationResult.username,
      };
      onDataChange(integration);
    }
  }, [isValid, validationResult, pat, onDataChange]);

  const handleNext = useCallback(async () => {
    if (!isValid || !validationResult || isValidating) return;

    try {
      // Save settings (user details + GitHub PAT) before proceeding
      await saveSettingsMutation.mutateAsync({
        version: '1.0.0',
        user: {
          firstName: userDetails.firstName,
          lastName: userDetails.lastName,
          ldapUsername: userDetails.ldapUsername,
        },
        integrations: {
          github: {
            pat,
            emuSuffix: validationResult.emu_suffix,
            username: validationResult.username,
          },
        },
        onboardingCompleted: false,
      });

      onNext();
    } catch (error) {
      console.error('Failed to save settings:', error);
      // TODO: Show error dialog to user
    }
  }, [isValid, validationResult, isValidating, pat, userDetails, saveSettingsMutation, onNext]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="mb-4 text-lg font-semibold text-foreground">
          Step 2: GitHub Integration
        </h2>

        {/* PAT Field */}
        <div className="mb-4">
          <label htmlFor="wizard-pat" className="mb-2 block text-sm font-medium text-foreground">
            Personal Access Token
          </label>

          <div className="relative">
            <input
              id="wizard-pat"
              type="password"
              {...register('pat')}
              onBlur={(e) => {
                void validate(e.target.value);
              }}
              onKeyDown={(e) => e.key === 'Enter' && void handleNext()}
              placeholder="Enter your PAT"
              className={`w-full rounded-lg border bg-background px-4 py-3 pr-10 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 ${
                validationError
                  ? 'border-destructive focus:ring-destructive'
                  : 'border-border focus:ring-primary'
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
              <p className="text-xs text-destructive">{validationError}</p>
            ) : (
              <p className="text-xs text-muted-foreground">
                This token will be used to authenticate with your project management tools.
              </p>
            )}
          </div>
        </div>

        {/* EMU Status Display */}
        {isValid && validationResult && (
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">
              Enterprise Managed User (EMU) Status
            </label>
            <div
              className={`rounded-lg border px-4 py-3 ${
                validationResult.emu
                  ? 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20'
                  : 'border-border bg-muted'
              }`}
            >
              {validationResult.emu && validationResult.emu_suffix ? (
                <div className="space-y-1">
                  <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    ✓ EMU User Detected
                  </p>
                  <p className="text-sm text-foreground">
                    Company Suffix:{' '}
                    <span className="font-mono font-semibold">{validationResult.emu_suffix}</span>
                  </p>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Not an EMU user</p>
              )}
            </div>
          </div>
        )}
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
          onClick={() => void handleNext()}
          disabled={!isValid || isValidating || saveSettingsMutation.isPending}
          className="flex items-center gap-2 rounded-lg bg-primary px-6 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-50"
          type="button"
        >
          {saveSettingsMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
          {saveSettingsMutation.isPending ? 'Saving...' : 'Next'}
        </button>
      </div>
    </div>
  );
};
