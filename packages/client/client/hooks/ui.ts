import { useEffect, useRef, useState } from 'react';

type MediaQueryCallback = (event: { matches: boolean; media: string }) => void;

/**
 * Older versions of Safari (shipped withCatalina and before) do not support addEventListener on matchMedia
 * https://stackoverflow.com/questions/56466261/matchmedia-addlistener-marked-as-deprecated-addeventlistener-equivalent
 * */
function attachMediaListener(
  query: MediaQueryList,
  callback: MediaQueryCallback
) {
  try {
    query.addEventListener('change', callback);
    return () => query.removeEventListener('change', callback);
  } catch (e) {
    query.addListener(callback);
    return () => query.removeListener(callback);
  }
}

function getInitialValue(query: string, initialValue?: boolean) {
  if (typeof initialValue === 'boolean') {
    return initialValue;
  }

  if (typeof window !== 'undefined' && 'matchMedia' in window) {
    return window.matchMedia(query).matches;
  }

  return false;
}

export function useMediaQuery(
  query: string,
  initialValue?: boolean,
  { getInitialValueInEffect } = {
    getInitialValueInEffect: true,
  }
) {
  const [matches, setMatches] = useState(
    getInitialValueInEffect
      ? initialValue
      : getInitialValue(query, initialValue)
  );
  const queryRef = useRef<MediaQueryList>();

  useEffect(() => {
    if ('matchMedia' in window) {
      queryRef.current = window.matchMedia(query);
      setMatches(queryRef.current.matches);
      return attachMediaListener(queryRef.current, (event) =>
        setMatches(event.matches)
      );
    }

    return undefined;
  }, [query]);

  return matches;
}

// Should match the breakpoints in the theme set in semantic/src/site/globals/site.variables
export function useBreakpoints() {
  const isMobileMin = useMediaQuery('(min-width: 320px)');
  const isMobileMax = useMediaQuery('(max-width: 767px)');
  const isMobile = isMobileMin && isMobileMax;

  const isTabletMin = useMediaQuery('(min-width: 768px)');
  const isTabletMax = useMediaQuery('(max-width: 991px)');
  const isTablet = isTabletMin && isTabletMax;

  const isComputerMin = useMediaQuery('(min-width: 992px)');
  const isComputerMax = useMediaQuery('(max-width: 1199px)');
  const isComputer = isComputerMin && isComputerMax;

  const isLargeMonitorMin = useMediaQuery('(min-width: 1200px)');
  const isLargeMonitorMax = useMediaQuery('(max-width: 1919px)');
  const isLargeMonitor = isLargeMonitorMin && isLargeMonitorMax;

  const isWidescreenMonitorMin = useMediaQuery('(min-width: 1920px)');
  const isWidescreenMonitor = isWidescreenMonitorMin;

  return {
    isMobileMin,
    isMobileMax,
    isMobile,
    isTabletMin,
    isTabletMax,
    isTablet,
    isComputerMin,
    isComputerMax,
    isComputer,
    isLargeMonitorMin,
    isLargeMonitorMax,
    isLargeMonitor,
    isWidescreenMonitorMin,
    isWidescreenMonitor,
  };
}

export function useHijackHistory(
  active: boolean,
  onBack?: () => void,
  { onlyOnMobile = true } = {} as { onlyOnMobile?: boolean }
) {
  const { isMobileMax } = useBreakpoints();

  const ignore = onlyOnMobile && !isMobileMax;

  const [pushed, setPushed] = useState(false);

  useEffect(() => {
    if (ignore) return;

    if (active) {
      const prev = window.onpopstate;
      if (!pushed) {
        console.debug('useHijackHistory', 'push');

        window.history.pushState(null, '', window.location.href + '#momo');
        setPushed(true);
      }
      window.onpopstate = () => {
        setPushed(false); // prevents popping twice
        console.debug('useHijackHistory', 'back');
        if (onBack) {
          console.debug('useHijackHistory', 'onBack');
          onBack();
        } else {
          console.debug('useHijackHistory', 'click');
          document.body.click();
        }
      };

      return () => {
        window.onpopstate = prev;
      };
    } else {
      if (pushed) {
        console.debug('useHijackHistory', 'pop');
        window.history.back();
        setPushed(false);
      }
    }
  }, [active, onBack, ignore]);
}
