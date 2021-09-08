import { getCookies, removeCookies, setCookies } from '../misc/utility';

export const localStorageEffect = (key, options?: { session?: boolean }) => ({
  setSelf,
  onSet,
}) => {
  const storage = options?.session ? sessionStorage : localStorage;

  const savedValue = storage.getItem(key);

  if (savedValue != null) {
    setSelf(JSON.parse(savedValue));
  }

  onSet((newValue) => {
    storage.setItem(key, JSON.stringify(newValue));
  });
};

export const cookieEffect = (
  key,
  options?: Parameters<typeof setCookies>[3] & {
    noInitialValue?: boolean;
    removeIfNoInitialValue?: boolean;
  }
) => ({ setSelf, onSet }) => {
  const savedValue = getCookies(undefined, key);

  if (savedValue !== undefined && options?.noInitialValue) {
    setSelf(savedValue);
  } else if (options?.removeIfNoInitialValue) {
    removeCookies(undefined, key);
  }

  onSet((newValue) => {
    setCookies(undefined, key, newValue);
  });
};
