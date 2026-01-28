/**
 * Onboarding Wizard - Main orchestrator component
 */

import { useState, useCallback } from 'react';
import { Modal } from '@libs/shared/ui/modal';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@libs/shared/hooks/use-theme';
import { StepUserDetails } from './step-user-details';
import { StepIntegrations } from './step-integrations';
import { StepTeamMembers } from './step-team-members';
import type { UserDetails, GitHubIntegration } from './types';

interface OnboardingWizardProps {
  isOpen: boolean;
  onComplete: () => void;
}

export const OnboardingWizard = ({ isOpen, onComplete }: OnboardingWizardProps) => {
  const [step, setStep] = useState(1);
  const [userDetails, setUserDetails] = useState<UserDetails>({
    firstName: '',
    lastName: '',
    ldapUsername: '',
  });
  const [githubIntegration, setGithubIntegration] = useState<GitHubIntegration>({
    pat: '',
  });

  const { isDarkMode, toggleTheme } = useTheme();

  const handleClose = useCallback(() => {
    // Wizard cannot be dismissed - user must complete setup
  }, []);

  const handleUserDetailsChange = useCallback((data: UserDetails) => {
    setUserDetails(data);
  }, []);

  const handleUserDetailsNext = useCallback(() => {
    setStep(2);
  }, []);

  const handleIntegrationsNext = useCallback(() => {
    setStep(3);
  }, []);

  const handleIntegrationsBack = useCallback(() => {
    setStep(1);
  }, []);

  const handleTeamMembersBack = useCallback(() => {
    setStep(2);
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
        <div className="relative text-center">
          <h1 className="text-2xl font-bold text-foreground">Welcome to Falcon IQ</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Let's get you set up in just a few steps
          </p>

          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className="absolute right-0 top-0 rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
            aria-label={isDarkMode ? 'Switch to light mode' : 'Switch to dark mode'}
            type="button"
          >
            {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
        </div>

        {/* Progress Indicator */}
        <div className="flex items-center justify-center gap-2">
          <div
            className={`h-2 w-24 rounded-full transition-colors ${
              step >= 1 ? 'bg-primary' : 'bg-muted'
            }`}
          />
          <div
            className={`h-2 w-24 rounded-full transition-colors ${
              step >= 2 ? 'bg-primary' : 'bg-muted'
            }`}
          />
          <div
            className={`h-2 w-24 rounded-full transition-colors ${
              step >= 3 ? 'bg-primary' : 'bg-muted'
            }`}
          />
        </div>

        {/* Step Components */}
        {step === 1 && (
          <StepUserDetails
            userDetails={userDetails}
            onNext={handleUserDetailsNext}
            onDataChange={handleUserDetailsChange}
          />
        )}

        {step === 2 && (
          <StepIntegrations
            userDetails={userDetails}
            githubIntegration={githubIntegration}
            onNext={handleIntegrationsNext}
            onBack={handleIntegrationsBack}
            onDataChange={setGithubIntegration}
          />
        )}

        {step === 3 && (
          <StepTeamMembers
            userDetails={userDetails}
            githubIntegration={githubIntegration}
            onBack={handleTeamMembersBack}
            onComplete={onComplete}
          />
        )}
      </div>
    </Modal>
  );
};
