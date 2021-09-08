import { DrawerTab } from '../misc/enums';
import StateBlock, { defineAtom } from './_base';
import { localStorageEffect } from './_statehelpers';

export default class _AppState extends StateBlock {
  static properties = defineAtom({
    default: {
      special_namespace: '__namespace__',
    },
  });

  static theme = defineAtom({
    default: 'light' as 'light' | 'dark',
  });

  static sameMachine = defineAtom({ default: false });

  static home = defineAtom({ default: '/library' });

  static loggedIn = defineAtom({ default: false });

  static externalViewer = defineAtom({
    default: false,
    effects_UNSTABLE: [localStorageEffect('external_viewer')],
  });

  static sidebarWidth = defineAtom({
    default: 'very thin' as 'very thin' | 'thin',
  });

  static drawerOpen = defineAtom({ default: false });
  static drawerTab = defineAtom({
    default: DrawerTab.Queue,
    effects_UNSTABLE: [localStorageEffect('drawing_tab')],
  });

  static readingQueue = defineAtom({
    default: [] as number[],
    effects_UNSTABLE: [localStorageEffect('reading_queue', { session: true })],
  });
}
