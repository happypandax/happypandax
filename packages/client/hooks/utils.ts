import { DependencyList, useRef, RefObject, useEffect } from 'react';

export function useDocumentEvent<E extends keyof HTMLElementEventMap, F>(
  name: E,
  func: (this: HTMLElement, ev: HTMLElementEventMap[E]) => any,
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

export function useRefEvent<
  R extends HTMLElement,
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
