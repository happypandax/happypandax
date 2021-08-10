import StateBlock, { defineAtom } from './_base';

const localStorageEffect = (key, session = false) => ({ setSelf, onSet }) => {
  const storage = session ? sessionStorage : localStorage;

  const savedValue = storage.getItem(key);

  if (savedValue != null) {
    setSelf(JSON.parse(savedValue));
  }

  onSet((newValue) => {
    storage.setItem(key, JSON.stringify(newValue));
  });
};

export default class _AppState extends StateBlock {
  static theme = defineAtom({
    default: 'light' as 'light' | 'dark',
  });

  static home = defineAtom({ default: '/library' });

  static loggedIn = defineAtom({ default: false });

  static drawerOpen = defineAtom({ default: false });

  static readingSession = defineAtom({
    default: [] as number[],
    effects_UNSTABLE: [localStorageEffect('reading_session', true)],
  });
}
