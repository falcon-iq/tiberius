import { createRouter, RouterProvider } from '@tanstack/react-router';
import { createHashHistory } from '@tanstack/react-router';

// Import the generated route tree
import { routeTree } from '@generatedtypes/routeTree.gen';

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
  return <RouterProvider router={router} />;
};

export default App;
