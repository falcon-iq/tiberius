import { createRouter, RouterProvider } from '@tanstack/react-router';
import { createHashHistory } from '@tanstack/react-router';
import { useState } from 'react';
import { AppProviders } from '@providers/index';

// Import the generated route tree
import { routeTree } from '@generatedtypes/routeTree.gen';
// TEMPORARY: Import wizard for testing
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

const App = () => {
  // TEMPORARY: State for testing the onboarding wizard
  const [showWizard, setShowWizard] = useState(true);

  const handleWizardComplete = (pat: string, users: string[]) => {
    console.log('Wizard completed!');
    console.log('PAT:', pat);
    console.log('Users:', users);
    setShowWizard(false);
  };

  return (
    <AppProviders>
      <RouterProvider router={router} />
      {/* TEMPORARY: Wizard for testing - remove after testing */}
      <OnboardingWizard isOpen={showWizard} onComplete={handleWizardComplete} />
    </AppProviders>
  );
};

export default App;
