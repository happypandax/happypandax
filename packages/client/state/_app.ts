import { DrawerTab } from '../misc/enums';
import { NotificationData } from '../misc/types';
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

  static connected = defineAtom({ default: false });
  static loggedIn = defineAtom({ default: false });

  static externalViewer = defineAtom({
    default: false,
    effects_UNSTABLE: [localStorageEffect('external_viewer')],
  });

  static blur = defineAtom({
    default: true,
    effects_UNSTABLE: [localStorageEffect('blur')],
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

  static notifications = defineAtom({
    default: [] as NotificationData[],
    effects_UNSTABLE: [
      ({ setSelf, onSet }) => {
        onSet((newValue) => {
          if (newValue.length > 15) {
            setSelf(newValue.slice(15));
          }
        });
      },
    ],
  });

  static notificationAlert = defineAtom({
    default: [] as NotificationData[],
    effects_UNSTABLE: [
      ({ setSelf, onSet }) => {
        onSet((newValue) => {
          if (notifID) {
            clearTimeout(notifID);
          }

          if (newValue.length) {
            notifID = setTimeout(() => setSelf([]), 1000 * 30);
          }

          if (newValue.length > 5) {
            setSelf(newValue.slice(5));
          }
        });
      },
    ],
  });
}

let notifID = undefined;
