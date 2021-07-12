import Router from 'next/router';
import querystring, {
  ParsedUrl,
  StringifiableRecord,
  StringifyOptions,
} from 'query-string';

import { Marked, Renderer } from '@ts-stack/markdown';

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

export function urlstring(
  querypath: StringifiableRecord | string,
  query?: StringifiableRecord,
  options?: StringifyOptions
) {
  const path = typeof querypath === 'string' ? querypath : undefined;
  const q = typeof querypath !== 'string' ? querypath : query;
  return querystring.stringifyUrl(
    {
      url: path ?? Router.pathname,
      query: {
        ...(path ? {} : Router.query),
        ...q,
      },
    },
    options
  );
}

export function urlparse(
  url?: string
): Omit<ParsedUrl, 'query'> & {
  query: Record<
    string,
    string | string[] | number[] | number | boolean | boolean[]
  >;
} {
  let u = url ?? Router.asPath;

  return querystring.parseUrl(u, {
    parseBooleans: true,
    parseNumbers: true,
    parseFragmentIdentifier: true,
  }) as any;
}
