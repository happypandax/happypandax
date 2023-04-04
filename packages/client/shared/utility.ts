import { JsonMap } from 'happypandax-client';
import _ from 'lodash';
import querystring, {
  ParsedUrl,
  StringifiableRecord,
  StringifyOptions,
} from 'query-string';

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

  const dpath =
    typeof window !== 'undefined'
      ? window.location.pathname + window.location.search
      : '';

  return querystring.stringifyUrl(
    {
      url: path ?? dpath,
      query: formatQuery({
        ...(path ? {} : (urlparse(dpath).query as StringifiableRecord)),
        ...q,
      }),
    },
    { ...options, arrayFormat: 'index' }
  );
}

export function urlparse(url?: string): Omit<ParsedUrl, 'query'> & {
  query: Record<
    string,
    string | string[] | number[] | number | boolean | boolean[] | JsonMap
  >;
} {
  let u =
    url ??
    (typeof window !== 'undefined'
      ? window.location.pathname + window.location.search
      : '');

  const r = querystring.parseUrl(u, {
    parseBooleans: true,
    parseNumbers: true,
    parseFragmentIdentifier: true,
    arrayFormat: 'index',
  }) as any;
  r.query = unformatQuery(r.query);
  return r;
}

export function pauseUntil(
  condition: () => boolean,
  interval = 100,
  timeout = Infinity
) {
  return new Promise<true>((resolve, reject) => {
    let timeoutId: NodeJS.Timeout;

    const check = () => {
      if (condition()) {
        clearTimeout(timeoutId);
        resolve(true);
      } else {
        timeoutId = setTimeout(check, interval);
      }
    };

    check();

    setTimeout(() => {
      clearTimeout(timeoutId);
      reject(new Error('Timeout'));
    }, timeout);
  });
}

/**
 * Format bytes as human-readable text.
 *
 * @param bytes Number of bytes.
 * @param si True to use metric (SI) units, aka powers of 1000. False to use
 *           binary (IEC), aka powers of 1024.
 * @param dp Number of decimal places to display.
 *
 * @return Formatted string.
 */
export function humanFileSize(bytes, si = false, dp = 1) {
  const thresh = si ? 1000 : 1024;

  if (Math.abs(bytes) < thresh) {
    return bytes + ' B';
  }

  const units = si
    ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
  let u = -1;
  const r = 10 ** dp;

  do {
    bytes /= thresh;
    ++u;
  } while (
    Math.round(Math.abs(bytes) * r) / r >= thresh &&
    u < units.length - 1
  );

  return bytes.toFixed(dp) + ' ' + units[u];
}

type DebounceArgs = Parameters<typeof _.debounce>;

/**
 * Like _.debounce, but collects all the arguments from each call in an array and passes them to the callback
 */
export function debounceCollect<P extends any[], T extends (args: P) => any>(
  fn: T,
  wait: DebounceArgs[1],
  {
    maxSize = Infinity,
    ...debounceOptions
  }: { maxSize?: number } & DebounceArgs[2] = {}
): _.DebouncedFunc<T> {
  const args = [] as P;

  const runFn = () => {
    const r = fn(args);
    args.length = 0;
    return r;
  };

  const debounced = _.debounce(runFn, wait, debounceOptions);

  const cancel = () => {
    debounced.cancel();

    args.length = 0;
  };

  const queuedDebounce = (a: P) => {
    args.push(...a);

    if (args.length >= maxSize) debounced.flush();
    else return debounced();
  };

  queuedDebounce.cancel = cancel;

  queuedDebounce.flush = debounced.flush;

  return queuedDebounce;
}

export function defined(value) {
  return value !== undefined;
}

export function JSONSafe<T extends Record<any, any>>(obj: T) {
  const o = { ...obj };
  Object.entries(obj).forEach(([k, v]) => {
    if (v === undefined) {
      delete o[k];
    }
  });
  return o;
}

export function maskText(text: string) {
  return text
    .split(' ')
    .map((s) =>
      s
        .split('')
        .map((c) => _.sample(['▀', '█', '▍', '▆', '▃']))
        .join()
    )
    .join(' ');
}

/**
 * Rounds a number to the nearest multiple of another number
 */
export function roundToNearest(n: number, nearest: number = 1) {
  return Math.round(n / nearest) * nearest;
}

export function asyncDebounce<F extends (...args: any[]) => Promise<any>>(
  func: F,
  wait?: number
) {
  const debounced = _.debounce(async (resolve, reject, bindSelf, args) => {
    try {
      const result = await func.bind(bindSelf)(...args);
      resolve(result);
    } catch (error) {
      reject(error);
    }
  }, wait);

  // This is the function that will be bound by the caller, so it must contain the `function` keyword.
  function returnFunc(...args) {
    return new Promise((resolve, reject) => {
      debounced(resolve, reject, this, args);
    });
  }

  return returnFunc as F;
}
