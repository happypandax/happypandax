/**
 * Difference between global state and other states is that global state does not depend on the react context or runtime
 */

import { autorun, get, makeAutoObservable, set, toJS } from 'mobx';
import { enableStaticRendering } from 'mobx-react-lite';
import { useEffect, useState } from 'react';

import {
  DISABLE_SERVER_CONNECT,
  HPX_SERVER_HOST,
  HPX_SERVER_PORT,
} from '../server/constants';
import { ServerUser } from '../shared/types';

import type { ActivityMap } from '../client/activity';
/**
 * Call enableStaticRendering(true) when running in an SSR environment, in which observer wrapped components should never re-render,
 * but cleanup after the first rendering automatically. Use isUsingStaticRendering() to inspect the current setting.
 */
enableStaticRendering(typeof window === 'undefined');

class State {
  initialized = false;

  packageJson: Record<string, any> = {};

  disableServerConnect = DISABLE_SERVER_CONNECT;
  serverHost: string = HPX_SERVER_HOST;
  serverPort: number = HPX_SERVER_PORT;

  connected = false;
  debug = process.env.NODE_ENV !== 'production';
  sameMachine = false;
  loggedIn = false;
  user: ServerUser | null = null;

  activity: ActivityMap = {};

  constructor() {
    makeAutoObservable(this, undefined, {
      deep: false,
    });
  }

  setState<T extends StateKey>(state: { [key in T]?: State[key] }) {
    const S: State = this;
    for (const key of Object.keys(state)) {
      set(this, key, state[key]);
    }
  }
}

// TODO: filter out functions
type StateKey = keyof State;

export const GlobalState = new State();

export const useGlobalState = <T extends StateKey>(
  state: T
): [State[T], (v: State[T]) => void] => {
  const [value, setValue] = useState<State[T]>(toJS(get(GlobalState, state)));

  useEffect(() => {
    const dispose = autorun(() => {
      setValue?.(toJS(get(GlobalState, state)));
    });
    return () => dispose();
  }, [state]);

  return [value, (newValue) => GlobalState.setState({ [state]: newValue })];
};

export const useGlobalValue = <T extends StateKey>(state: T) => {
  return useGlobalState<T>(state)[0];
};

export const useSetGlobalState = <T extends StateKey>(state: T) => {
  return useGlobalState<T>(state)[1];
};

type ValuesOf<T extends any[]> = T[number];

export function onGlobalStateChange<S extends StateKey[]>(
  states: S,
  callback: (state: { [key in ValuesOf<S>]: State[key] }) => void
) {
  if (typeof window === 'undefined') {
    return () => {};
  }

  return autorun(() => {
    const s = {} as { [key in ValuesOf<S>]: State[key] };
    for (const state of states) {
      s[state] = toJS(get(GlobalState, state));
    }

    callback(s);
  });
}
