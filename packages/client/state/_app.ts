import type { ActivityMap } from '../client/activity';
import { DrawerTab, ItemType } from '../shared/enums';
import { ItemID, NotificationData, ThemeValue } from '../shared/types';
import StateBlock, { defineAtom, defineSelector } from './_base';
import { localStorageEffect } from './_statehelpers';

export default class _AppState extends StateBlock {
  static properties = defineAtom({
    default: {
      special_namespace: '__namespace__',
    },
  });

  static theme = defineAtom({
    default: 'momo-l' as ThemeValue,
    effects: [localStorageEffect('theme')],
  });

  static home = defineAtom({
    default: '/library',
    effects: [localStorageEffect()],
  });


  static externalViewer = defineAtom({
    default: false,
    effects: [localStorageEffect('external_viewer')],
  });

  static blur = defineAtom({
    default: true,
    effects: [localStorageEffect('blur')],
  });
  static drawerButtonPosition = defineAtom({
    default: 'left' as 'left' | 'right',
    effects: [localStorageEffect()],
  });

  static sidebarWidth = defineAtom({
    default: 'very thin' as 'very thin' | 'thin',
  });

  static sidebarForcePosition = defineAtom({
    default: undefined as 'left' | 'right' | undefined,
    effects: [localStorageEffect()],
  });

  static sidebarPosition = defineAtom({
    default: 'left' as 'left' | 'right',
    effects: [
      ({ setSelf, getLoadable }) => {
        const v = getLoadable(_AppState.sidebarForcePosition).getValue();
        if (v) {
          setSelf(v);
        }
      },
    ],
  });

  static sidebarHidden = defineAtom({
    default: false,
  });

  static drawerSticky = defineAtom({ default: false });
  static drawerExpanded = defineAtom({ default: false });
  static drawerOpen = defineAtom({
    default: false,
    effects: [
      ({ setSelf, onSet, getLoadable }) => {
        onSet((newValue) => {
          if (!getLoadable(_AppState.drawerSticky).getValue()) {
            setSelf(newValue);
          }
        });
      },
    ],
  });
  static drawerTab = defineAtom({
    default: DrawerTab.Queue,
    effects: [localStorageEffect('drawing_tab')],
  });

  static readingQueue = defineAtom({
    default: [] as number[],
    effects: [localStorageEffect('reading_queue', { session: true })],
  });

  static notifications = defineAtom({
    default: [] as NotificationData[],
    effects: [
      ({ setSelf, onSet }) => {
        onSet((newValue) => {
          if (newValue.length > 15) {
            setSelf(newValue.slice(0, 15));
          }
        });
      },
    ],
  });

  static notificationAlert = defineAtom({
    default: [] as NotificationData[],
    effects: [
      ({ setSelf, onSet }) => {
        onSet((newValue) => {
          if (notifID) {
            clearTimeout(notifID);
          }

          if (newValue.length) {
            notifID = setTimeout(() => setSelf([]), 1000 * 30);
          }

          if (newValue.length > 5) {
            setSelf(newValue.slice(0, 5));
          }
        });
      },
    ],
  });

  static itemActivityState = defineAtom({
    default: {} as ActivityMap,
  });

  static itemActivity = defineSelector(
    {
      get:
        ({ type, item_id }: { type: ItemType; item_id: ItemID }) =>
          ({ get }) => {
            const state = get(_AppState.itemActivityState);

            if (type && item_id && state[type] && state[type][item_id]) {
              return state[type][item_id];
            }
            return [];
          },
      cachePolicy_UNSTABLE: { eviction: 'lru', maxSize: 250 },
    },
    true
  );
}

let notifID = undefined;
