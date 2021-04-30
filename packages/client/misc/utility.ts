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
    scrollToElement(document.getElementById('root'));
  }
}

export function scrollToElement(element: HTMLElement, smooth = true) {
  element.scrollIntoView({
    behavior: smooth ? 'smooth' : 'auto',
  });
}
