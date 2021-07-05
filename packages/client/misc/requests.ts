import { NextApiRequest, NextApiResponse } from 'next';
import nextConnect, { Options } from 'next-connect';

export function handler(options?: Options<NextApiRequest, NextApiResponse>) {
  return nextConnect<NextApiRequest, NextApiResponse>(options);
}
