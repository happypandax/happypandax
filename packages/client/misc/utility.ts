export { default as update } from 'immutability-helper';
import cookie from 'cookie';
import { format, formatDistanceToNowStrict, fromUnixTime } from 'date-fns';
import { JsonMap } from 'happypandax-client';
import { NextPageContext } from 'next';
import Router from 'next/router';
import querystring, {
  ParsedUrl,
  StringifiableRecord,
  StringifyOptions,
} from 'query-string';

import { Marked, Renderer } from '@ts-stack/markdown';

import t from './lang';

Marked.setOptions({
  renderer: new Renderer(),
  gfm: true,
  tables: true,
  breaks: false,
  pedantic: false,
  sanitize: false,
  smartLists: true,
  smartypants: false,
});

export function parseMarkdown(txt: string) {
  return Marked.parse(txt);
}

export function getEnumMembers<T>(myEnum: T): (keyof T)[] {
  return Object.keys(myEnum).filter(
    (k) => typeof (myEnum as any)[k] === 'number'
  ) as any;
}

export function getEnumMembersMKeyMap<T>(myEnum: T): { [s: string]: keyof T } {
  const obj: { [s: string]: keyof T } = {};
  // eslint-disable-next-line no-restricted-syntax
  for (const key of getEnumMembers(myEnum)) {
    obj[key as string] = key;
  }

  return obj;
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

function formatQuery(query: StringifiableRecord) {
  const q = { ...query };
  Object.entries(q).forEach(([k, v]) => {
    if (typeof v === 'object') {
      q[k] = JSON.stringify(v);
    }
  });
  return q;
}

function unformatQuery(query: StringifiableRecord) {
  const q = { ...query };
  Object.entries(q).forEach(([k, v]) => {
    if (typeof v === 'string') {
      try {
        q[k] = JSON.parse(v);
      } catch {}
    }
  });
  return q;
}

export function urlstring(
  querypath?: StringifiableRecord | string,
  query?: StringifiableRecord,
  options?: StringifyOptions
) {
  const path = typeof querypath === 'string' ? querypath : undefined;
  const q = typeof querypath !== 'string' && querypath ? querypath : query;

  return querystring.stringifyUrl(
    {
      url: path ?? Router.pathname,
      query: formatQuery({
        ...(path ? {} : Router.query),
        ...q,
      }),
    },
    { ...options, arrayFormat: 'index' }
  );
}

export function urlparse(
  url?: string
): Omit<ParsedUrl, 'query'> & {
  query: Record<
    string,
    string | string[] | number[] | number | boolean | boolean[] | JsonMap
  >;
} {
  let u = url ?? Router.asPath;

  const r = querystring.parseUrl(u, {
    parseBooleans: true,
    parseNumbers: true,
    parseFragmentIdentifier: true,
    arrayFormat: 'index',
  }) as any;
  r.query = unformatQuery(r.query);
  return r;
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
    if (v === undefined) return undefined;
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
