import { useMemo, useState } from 'react';

import { ServerItemWithProfile } from '../../misc/types';

const defaultImage = '/img/default.png';
const errorImage = '/img/error-image.png';
const noImage = '/img/no-image.png';

export type ImageSource = string | ServerItemWithProfile['profile'];

export function useImage(initialSrc?: ImageSource) {
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(initialSrc ? false : true);
  const src = useMemo(() => {
    if (error) {
      return errorImage;
    }

    const s = !initialSrc
      ? noImage
      : typeof initialSrc === 'string'
      ? initialSrc
      : initialSrc.data
      ? initialSrc.data
      : noImage;

    if (loaded) {
      return s;
    }

    const img = new Image();
    img.src = s;
    if (img.complete) {
      return s;
    }
    img.addEventListener('load', () => setLoaded(true));
    img.addEventListener('error', () => setError(true));

    return defaultImage;
  }, [initialSrc, loaded, error]);

  return { src, loaded, setLoaded, error, setError };
}
