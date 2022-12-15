import { NextApiRequest, NextApiResponse } from 'next';
import nextConnect, { NextHandler, Options } from 'next-connect';
import nextSession from 'next-session';

import { FetchQueryOptions, QueryClient } from '@tanstack/query-core';

import { ServiceType } from '../services/constants';
import { MomoActions, MomoType, QueryActions } from '../shared/query';
import { urlparse, urlstring } from '../shared/utility';

import type { CallOptions } from '../services/server';
export interface RequestOptions extends CallOptions {
  notifyError?: boolean;
}

export interface ErrorResponseData {
  error: string;
  code: number;
}

function onError(
  err: any,
  req: NextApiRequest,
  res: NextApiResponse<any>,
  next: NextHandler
) {
  let __options: RequestOptions;

  if (req.body) {
    __options = req.body.__options as RequestOptions;
  } else {
    __options = urlparse(req.url).query?.__options as RequestOptions;
  }

  if ((__options as RequestOptions)?.notifyError !== false) {
    const fairy = global.app.service.get(ServiceType.Fairy);
    fairy.notify({
      type: 'error',
      title: err?.code ? `Server [${err.code}]` : 'Client Error',
      body: err?.message,
    });
  }

  res.status(500).json({ error: err.message, code: err?.code ?? 0 });
}

export function handler(options?: Options<NextApiRequest, NextApiResponse>) {
  return nextConnect<NextApiRequest, NextApiResponse>({
    onError,
    ...options,
  });
}

export const getSession = nextSession({});

const serverQueryClient = new QueryClient({
  defaultOptions: {
    mutations: {
      retry: () => false,
    },
    queries: {
      retry: () => false,
      networkMode: 'always',
      staleTime: 0,
      cacheTime: 0,
    },
  },
})

type Actions<A> = MomoActions<A> | QueryActions<A>;

export async function fetchQuery<
  A = undefined,
  T extends Actions<A> = Actions<A>,
  K extends T['type'] = T['type'],
  V extends Extract<T, { type: K }>['variables'] = Extract<
    T,
    { type: K }
  >['variables'],
  R extends Extract<T, { type: K }>['dataType'] = Extract<
    T,
    { type: K }
  >['dataType']>
  (
    action: K,
    variables?: V,
    options?: FetchQueryOptions<R | null>,
    config?: RequestInit
  ): Promise<R | null> {
  const key = [action.toString(), variables];

  let endpoint = action.toString();

  let params: Partial<V> = variables;

  let method: RequestInit['method'] = 'GET'
  let data: Record<string, any> = undefined;

  switch (action as unknown as MomoType) {
    case MomoType.SAME_MACHINE: {
      endpoint = '/api/server/momo'
      method = 'POST'
      data = { action, ...variables }
      params = {}
      break;
    }
  }

  const url = urlstring(endpoint, params as any)


  const cfg: RequestInit = {
    method,
    body: JSON.stringify(data),
    ...config
  }

  return serverQueryClient.fetchQuery(
    key,
    ({ signal }): Promise<R | null> => {
      return fetch(url, cfg).then(async (response) => {
        const is_json = response.headers.get('content-type')?.includes('application/json');
        const data = is_json ? await response.json() : null;

        if (!response.ok) {
          const error = (data && data.error) || response.status;
          throw Error(error)
        }
        return data;
      })

    },
    options
  );
}
