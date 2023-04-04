import '../semantic/dist/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';

import { useMemo } from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { RecoilRoot } from 'recoil';
import { withThemes } from 'storybook-addon-themes/react'; // <- or your storybook framework

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import Theme from '../components/Theme';
import { AppState } from '../state';

export const parameters = {
  actions: { argTypesRegex: '^on[A-Z].*' },
  themes: {
    default: 'dark',
    list: [
      { name: 'light', color: '#FFEBEB' },
      { name: 'dark', color: '#373737' },
    ],
    Decorator: ({ themeName, children }) => (
      <Theme name={themeName}>{children}</Theme>
    ),
  },
};

export const decorators = [
  withThemes,
  // doesnt work for some reason??? can't figure out why
  // (Story) => {
  //   return (
  //     <AppRoot>
  //       <Story />
  //     </AppRoot>
  //   );
  // },

  (Story) => {
    const queryClient = useMemo(() => {
      return new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: Infinity,
          },
        },
      });
    }, []);

    return (
      <QueryClientProvider client={queryClient}>
        <RecoilRoot
          initializeState={(snapshot) => {
            snapshot.set(AppState.loggedIn, true);
          }}
        >
          <DndProvider backend={HTML5Backend}>
            <Story />
          </DndProvider>
        </RecoilRoot>
      </QueryClientProvider>
    );
  },
];
