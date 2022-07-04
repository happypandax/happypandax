import { NextApiRequest, NextApiResponse } from 'next';
import nextConnect, { NextHandler, Options } from 'next-connect';
import nextSession from 'next-session';

import { ServiceType } from '../services/constants';
import { CallOptions } from '../services/server';
import { urlparse } from './utility';

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
