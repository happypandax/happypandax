'use client';
import cookie from 'cookie';
import { format, formatDistanceToNowStrict, fromUnixTime } from 'date-fns';
import imupdate, { CustomCommands, extend, Spec } from 'immutability-helper';
import { NextPageContext } from 'next';

import { Marked, Renderer } from '@ts-stack/markdown';

import { ItemSort, ViewType } from '../shared/enums';
import t from './lang';

Marked.setOptions({
  renderer: new Renderer(),
  gfm: true,
  tables: true,
  breaks: true,
  pedantic: false,
  sanitize: false,
  smartLists: true,
  smartypants: true,
});

extend(
  '$insert',
  function (value: [index: number, value: any], original: any[]) {
    // invariant(Array.isArray(value),
    // () => `Expected $insert target to be an array; got ${value}`,)
    return imupdate(original, { $splice: [[value[0], 0, value[1]]] });
  }
);

extend('$removeIndex', function (value: number, original: any[]) {
  // invariant(Array.isArray(value),
  // () => `Expected $insert target to be an array; got ${value}`,)
  return imupdate(original, { $splice: [[value, 1]] });
});

interface UpdateCommands<T> {
  $insert: T extends Array<infer U> | ReadonlyArray<infer U>
  ? [index: number, value: any]
  : never;
  $removeIndex: T extends Array<infer U> | ReadonlyArray<infer U>
  ? number
  : never;
}

export function update<T>(
  object: T,
  spec: Spec<T, CustomCommands<UpdateCommands<T>>>
) {
  return imupdate(object, spec);
}

export function parseMarkdown(txt: string) {
  return Marked.parse(txt);
}

export function refreshPage() {
  if (location && location.reload) {
    location.reload();
  }
}

export function scrollToTop() {
  if (document) {
    scrollToElement(document.body);
  }
}

export function scrollToElement(element: HTMLElement, smooth = true) {
  element.scrollIntoView({
    behavior: smooth ? 'smooth' : 'auto',
  });
}

export function isElementInViewport(
  el: HTMLElement,
  opts?: { offset?: number }
) {
  const rect = el.getBoundingClientRect();

  const offset = opts?.offset || 0;

  return (
    rect.bottom >= 0 - offset &&
    rect.right >= 0 - offset &&
    rect.top <=
    (window.innerHeight || document.documentElement.clientHeight) + offset &&
    rect.left <=
    (window.innerWidth || document.documentElement.clientWidth) + offset
  );
}

// Replaces the URL without reloading unlike location.replace, also keeps state and title if unspecififed
export function replaceURL(
  url: string | URL,
  nextState?: any,
  nextTitle?: string
) {
  history.replaceState(
    nextState ?? history.state,
    nextTitle ?? window.document.title,
    url
  );
}

export function getClientWidth() {
  return window.innerWidth;
}

export function getClientHeight() {
  return window.innerHeight;
}

export function getScreenWidth() {
  return screen.width;
}

export function getScreenHeight() {
  return screen.height;
}

export const animateCSS = (
  node: HTMLElement,
  animation: string,
  prefixAnimation = true,
  prefix = 'animate__'
) =>
  // We create a Promise and return it
  new Promise((resolve, reject) => {
    const animationName = prefixAnimation ? `${prefix}${animation}` : animation;

    node.classList.add(`${prefix}animated`, animationName);

    // When the animation ends, we clean the classes and resolve the Promise
    function handleAnimationEnd(event) {
      event.stopPropagation();
      node.classList.remove(`${prefix}animated`, animationName);
      node.removeEventListener('animationend', handleAnimationEnd);
      resolve('Animation ended');
    }

    node.addEventListener('animationend', handleAnimationEnd, { once: true });
  });

export function setCookies(
  ctx: NextPageContext = undefined,
  key: string,
  data,
  options?: { expires?: number | Date }
) {
  if (typeof options?.expires === 'number') {
    options.expires = new Date(new Date() * 1 + options.expires * 864e5);
  }

  const cookieStr = cookie.serialize(key, JSON.stringify(data), {
    path: '/',
    sameSite: 'Lax',
    ...options,
  });
  if (global.app.IS_SERVER) {
    if (ctx && ctx.res) {
      const currentCookies = ctx.res.getHeader('Set-Cookie');

      ctx.res.setHeader(
        'Set-Cookie',
        !currentCookies ? [cookieStr] : currentCookies.concat(cookieStr)
      );

      if (ctx && ctx.req && ctx.req.cookies) {
        const _cookies = ctx.req.cookies;
        data === ''
          ? delete _cookies[key]
          : (_cookies[key] = JSON.stringify(data));
      }

      if (ctx && ctx.req && ctx.req.headers && ctx.req.headers.cookie) {
        const _cookies = cookie.parse(ctx.req.headers.cookie);

        data === ''
          ? delete _cookies[key]
          : (_cookies[key] = JSON.stringify(data));

        ctx.req.headers.cookie = Object.entries(_cookies).reduce(
          (accum, item) => {
            return accum.concat(`${item[0]}=${item[1]};`);
          },
          ''
        );
      }
    }
    return undefined;
  }

  document.cookie = cookieStr;
}

export function getCookies(ctx: NextPageContext | undefined, key?: string) {
  let _cookies = {};

  if (global.app.IS_SERVER) {
    if (ctx && ctx.req && ctx.req.cookies) {
      _cookies = ctx.req.cookies;
    }

    if (ctx && ctx.req && ctx.req.headers && ctx.req.headers.cookie) {
      _cookies = cookie.parse(ctx.req.headers.cookie);
    }
  } else {
    const documentCookies =
      !ctx && document?.cookie ? document?.cookie.split('; ') : [];

    for (let i = 0; i < documentCookies.length; i++) {
      const cookieParts = documentCookies[i].split('=');

      const _cookie = cookieParts.slice(1).join('=');
      const name = cookieParts[0];

      _cookies[name] = _cookie;
    }
  }

  if (key) {
    const v = _cookies[key];
    if (v === undefined || v === 'undefined') return undefined;
    return JSON.parse(decodeURIComponent(v));
  } else {
    return _cookies;
  }
}

export function removeCookies(
  ctx: NextPageContext = undefined,
  key: string,
  options?: {}
) {
  return setCookies(ctx, key, '', { ...options, expires: -1 });
}

export function dateFromTimestamp(
  timestamp: number,
  {
    relative = false,
    addSuffix = true,
    format: dateFormat = 'PPpp',
  }: { relative?: boolean; addSuffix?: boolean; format?: 'PPpp' | 'PPP' }
) {
  if (!timestamp) return t`Unknown`;
  const d = fromUnixTime(timestamp);
  return relative
    ? formatDistanceToNowStrict(d, { addSuffix })
    : format(d, dateFormat);
}

export function getLibraryQuery({
  favorites,
  filter,
  page,
  sort,
  sortDesc,
  query,
  limit,
  view,
}: {
  favorites?: boolean;
  filter?: number;
  page?: number;
  sort?: ItemSort;
  sortDesc?: boolean;
  limit?: number;
  query?: string;
  view?: ViewType;
}) {
  return {
    q: query,
    filter,
    sort,
    desc: sortDesc,
    p: page,
    fav: favorites,
    view,
    limit,
  };
}
