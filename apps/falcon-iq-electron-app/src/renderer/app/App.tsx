import { createRouter, RouterProvider } from '@tanstack/react-router';
import { createHashHistory } from '@tanstack/react-router';
import { useState, useEffect } from 'react';
import { AppProviders } from '@providers/index';
import { useSettings } from '@hooks/use-settings';

// Import the generated route tree
import { routeTree } from '@generatedtypes/routeTree.gen';
import { OnboardingWizard } from '@components/onboarding-wizard';

// Create hash history for Electron
const hashHistory = createHashHistory();

// Create a new router instance
const router = createRouter({
  routeTree,
  history: hashHistory,
});

// Register the router instance for type safety
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

const AppContent = () => {
  const { data: settings, isLoading } = useSettings();
  const [showWizard, setShowWizard] = useState(false);

  useEffect(() => {
    if (!isLoading && settings) {
      // Show wizard if onboarding not completed
      setShowWizard(!settings.onboardingCompleted);
    }
  }, [settings, isLoading]);

  const handleWizardComplete = () => {
    console.log('Wizard completed!');
    setShowWizard(false);
  };

  if (isLoading) {
    return null; // Or a loading spinner
  }

  return (
    <>
      <RouterProvider router={router} />
      {/* Key prop helps with HMR by forcing remount when wizard state changes */}
      <OnboardingWizard key="onboarding" isOpen={showWizard} onComplete={handleWizardComplete} />
    </>
  );
};

const App = () => {
  return (
    <AppProviders>
      <AppContent />
    </AppProviders>
  );
};

export default App;
