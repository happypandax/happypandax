import { withThemes } from 'storybook-addon-themes/react'; // <- or your storybook framework
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Theme } from '../components/Misc';
import '../semantic/dist/semantic.css';
import '../style/global.css';
import 'animate.css';
import 'react-virtualized/styles.css';

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
  (Story) => {
    return (
      <DndProvider backend={HTML5Backend}>
        <Story />
      </DndProvider>
    );
  },
];
