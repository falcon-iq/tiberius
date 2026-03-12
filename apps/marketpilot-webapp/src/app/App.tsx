import { createRouter, RouterProvider, createBrowserHistory } from '@tanstack/react-router';
import { AppProviders } from '@providers/index';
import { routeTree } from '@app-types/routeTree.gen';

const browserHistory = createBrowserHistory();

const router = createRouter({
  routeTree,
  history: browserHistory,
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

const App = () => {
  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  );
};

export default App;
