import { RecoilState, RecoilValue } from 'recoil';

import { getCookies, removeCookies, setCookies } from '../client/utility';

export const stateEffect = <T>(recoilValue: RecoilValue<T>) => ({ setSelf, onSet, getLoadable }) => {
  setSelf(getLoadable(recoilValue).getValue());
}

export const localStorageEffect =
  (
    key?: string | ((node: RecoilState<any>) => string),
    options?: { session?: boolean }
  ) =>
    ({ setSelf, onSet, node }) => {
      const storage = options?.session ? sessionStorage : localStorage;

      let k: string;
      if (typeof key === 'function') {
        k = key(node);
      } else if (!key) {
        k = node.key;
      } else {
        k = key;
      }

      const savedValue = storage.getItem(k);

      if (savedValue != null) {
        setSelf(savedValue !== 'undefined' ? JSON.parse(savedValue) : undefined);
      }

      onSet((newValue) => {
        storage.setItem(k, JSON.stringify(newValue));
      });
    };

export const cookieEffect =
  (
    key?: string | ((node: RecoilState<any>) => string),
    options?: Parameters<typeof setCookies>[3] & {
      noInitialValue?: boolean;
      removeIfNoInitialValue?: boolean;
    }
  ) =>
    ({ setSelf, onSet, node }) => {
      let k: string;
      if (typeof key === 'function') {
        k = key(node);
      } else if (!key) {
        k = node.key;
      } else {
        k = key;
      }

      const savedValue = getCookies(undefined, k);

      if (savedValue !== undefined) {
        if (!options?.noInitialValue) {
          setSelf(savedValue);
        }
      } else if (options?.removeIfNoInitialValue) {
        removeCookies(undefined, k);
      }

      onSet((newValue) => {
        setCookies(undefined, k, newValue);
      });
    };
