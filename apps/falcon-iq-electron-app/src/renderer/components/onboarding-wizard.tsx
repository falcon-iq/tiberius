import { useState, useCallback, useEffect } from 'react';
import { Modal } from '@libs/shared/ui';
import { Plus, Trash2, Sun, Moon } from 'lucide-react';

interface OnboardingWizardProps {
  isOpen: boolean;
  onComplete: (pat: string, users: string[]) => void;
}

export const OnboardingWizard = ({ isOpen, onComplete }: OnboardingWizardProps) => {
  const [step, setStep] = useState(1);
  const [pat, setPat] = useState('');
  const [users, setUsers] = useState<string[]>([]);
  const [newUser, setNewUser] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(false);

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
    if (newUser.trim() && !users.includes(newUser.trim())) {
      setUsers([...users, newUser.trim()]);
      setNewUser('');
    }
  }, [newUser, users]);

  const handleRemoveUser = useCallback((userToRemove: string) => {
    setUsers(users.filter((user) => user !== userToRemove));
  }, [users]);

  const handleNext = useCallback(() => {
    if (step === 1 && pat.trim()) {
      setStep(2);
    }
  }, [step, pat]);

  const handleComplete = useCallback(() => {
    if (users.length > 0) {
      onComplete(pat, users);
      // Reset state after completion
      setStep(1);
      setPat('');
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
              <label htmlFor="wizard-pat" className="mb-2 block text-sm font-medium text-foreground">
                Personal Access Token
              </label>
              <input
                id="wizard-pat"
                type="password"
                value={pat}
                onChange={(e) => setPat(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleNext()}
                placeholder="Enter your PAT"
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="mt-2 text-xs text-muted-foreground">
                This token will be used to authenticate with your project management tools.
              </p>
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleNext}
                disabled={!pat.trim()}
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
              <div className="mb-4 flex gap-2">
                <input
                  id="wizard-new-user"
                  type="text"
                  value={newUser}
                  onChange={(e) => setNewUser(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddUser()}
                  placeholder="Enter username"
                  className="flex-1 rounded-lg border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                />
                <button
                  onClick={handleAddUser}
                  className="rounded-lg bg-primary px-4 py-2 text-primary-foreground transition-colors hover:bg-primary/90"
                  type="button"
                  aria-label="Add user"
                >
                  <Plus className="h-5 w-5" />
                </button>
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
