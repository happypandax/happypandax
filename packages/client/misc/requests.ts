import { NextApiRequest, NextApiResponse } from 'next';
import nextConnect, { NextHandler, Options } from 'next-connect';
import nextSession from 'next-session';

import { FetchQueryOptions, QueryClient } from '@tanstack/react-query';

import { ServiceType } from '../services/constants';
import { QueryActions } from './query';
import { urlparse } from './utility';

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


export async function fetchQuery<
  A = undefined,
  T extends QueryActions<A> = QueryActions<A>,
  K extends T['type'] = T['type'],
  V extends Extract<T, { type: K }>['variables'] = Extract<
    T,
    { type: K }
  >['variables'],
  R extends Extract<T, { type: K }>['dataType'] = Extract<
    T,
    { type: K }
  >['dataType']>(
    action: K,
    variables?: V,
    options?: FetchQueryOptions<Response>,
    config?: RequestInit
  ) {
    const key = [action.toString(), variables];

}



fetch