import { NextApiRequest, NextApiResponse } from 'next';
import nextConnect, { NextHandler, Options } from 'next-connect';
import nextSession from 'next-session';

import { ServiceType } from '../services/constants';

function onError(
  err: any,
  req: NextApiRequest,
  res: NextApiResponse<any>,
  next: NextHandler
) {
  const fairy = global.app.service.get(ServiceType.Fairy);
  fairy.notify({
    type: 'error',
    title: err?.code ? `Server [${err.code}]` : 'Client Error',
    body: err?.message,
  });

  res.status(500).json({ error: err.message, code: err?.code });
}

export function handler(options?: Options<NextApiRequest, NextApiResponse>) {
  return nextConnect<NextApiRequest, NextApiResponse>({
    onError,
    ...options,
  });
}

export const getSession = nextSession({});
