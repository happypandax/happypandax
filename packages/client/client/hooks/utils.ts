import { action } from 'mobx';
import {
  DependencyList,
  EffectCallback,
  RefObject,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import { useUpdateEffect } from 'react-use';

export function useBodyEvent<E extends keyof HTMLBodyElementEventMap, F>(
  name: E,
  func: (this: HTMLBodyElement, ev: HTMLBodyElementEventMap[E]) => any,
  options?: boolean | AddEventListenerOptions,
  deps?: DependencyList,
  featureCheck?: () => boolean
) {
  if (featureCheck?.() ?? true) {
    useEffect(() => {
      document.body.addEventListener(name, func, options);

      return () => {
        document.body.removeEventListener(name, func);
      };
    }, deps);
  }
}

export function useDocumentEvent<E extends keyof DocumentEventMap, F>(
  name: E,
  func: (this: Document, ev: DocumentEventMap[E]) => any,
  options?: boolean | AddEventListenerOptions,
  deps?: DependencyList,
  featureCheck?: () => boolean
) {
  if (featureCheck?.() ?? true) {
    useEffect(() => {
      document.addEventListener(name, func, options);

      return () => {
        document.removeEventListener(name, func);
      };
    }, deps);
  }
}

export function useRefEvent<
  R extends HTMLElement | Document,
  E extends keyof HTMLElementEventMap
>(
  ref: RefObject<R>,
  name: E,
  func: (this: HTMLElement, ev: HTMLElementEventMap[E]) => any,
  options?: boolean | AddEventListenerOptions,
  deps?: DependencyList,
  featureCheck?: () => boolean
) {
  if (featureCheck?.() ?? true) {
    useEffect(() => {
      if (ref.current) {
        ref.current.addEventListener(name, func, options);
      }

      return () => {
        if (ref.current) {
          ref.current.removeEventListener(name, func);
        }
      };
    }, deps);
  }
}

export function useInterval(
  callback: Function,
  delay?: number | null,
  deps?: DependencyList
) {
  const savedCallback = useRef<Function>(() => {});

  useEffect(() => {
    savedCallback.current = callback;
  }, [deps]);

  useEffect(() => {
    if (delay !== null) {
      const interval = setInterval(() => savedCallback.current(), delay || 0);
      return () => clearInterval(interval);
    }

    return undefined;
  }, [delay]);
}

export function useTabActive() {
  const [active, setActive] = useState(true);

  useDocumentEvent(
    'visibilitychange',
    () => {
      setActive(document.visibilityState === 'visible');
    },
    {},
    []
  );

  return active;
}

/**
 *  useEffect, but wraps the effect in a mobx action
 */
export function useEffectAction(effect: EffectCallback, deps?: DependencyList) {
  useEffect(action(effect), deps);
}

/**
 *  useEffect, but wraps the effect in a mobx action
 */
export function useUpdateEffectAction(
  effect: EffectCallback,
  deps?: DependencyList
) {
  useUpdateEffect(action(effect), deps);
}

export function useTrackDimensions(
  effect: (entry: ResizeObserverEntry) => void,
  ref: RefObject<HTMLElement>,
  deps: DependencyList = []
) {
  const frame = useRef(0);

  const createObserver = useCallback(
    () =>
      new ResizeObserver((entries) => {
        const entry = entries[0];

        if (entry) {
          cancelAnimationFrame(frame.current);

          frame.current = requestAnimationFrame(() => {
            if (ref.current) {
              effect(entry);
            }
          });
        }
      }),
    [effect]
  );

  const [observer, setObserver] = useState(createObserver());

  useEffect(() => {
    setObserver(createObserver());
  }, [...deps]);

  useEffect(() => {
    observer.disconnect();

    if (ref.current) {
      observer.observe(ref.current);
    }
  }, [ref, observer]);
}
