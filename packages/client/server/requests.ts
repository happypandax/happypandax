import Cors, { CorsOptions } from 'cors';
import {
  AuthWrongCredentialsError,
  ConnectionError,
  ServerError,
} from 'happypandax-client';
import { IncomingMessage } from 'http';
import { NextApiRequest, NextApiResponse } from 'next';
import { NextAuthOptions } from 'next-auth';
import { getToken } from 'next-auth/jwt';
import CredentialsProvider from 'next-auth/providers/credentials';
import nextConnect, { NextHandler, Options } from 'next-connect';

import { FetchQueryOptions, QueryClient } from '@tanstack/query-core';

import { MomoActions, MomoType, QueryActions } from '../shared/query';
import { urlparse, urlstring } from '../shared/utility';
import {
  DISABLE_SERVER_CONNECT,
  HPX_DOMAIN_URL,
  HPX_SECRET,
  HPX_SERVER_HOST,
  HPX_SERVER_PORT,
  LOGIN_ERROR,
  ServiceType,
} from './constants';

import type { CallOptions } from '../services/server';
const corsOptions: CorsOptions = {
  origin: '*',
};

export interface RequestOptions extends CallOptions {
  notifyError?: boolean;
}

export interface ErrorResponseData {
  error: string;
  code: number;
}

function defaultOnError(
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

  if (process.env.NODE_ENV === 'development') {
    global.app.log.e(err);
  }

  if (!res.headersSent) {
    res.status(500).json({ error: err.message, code: err?.code ?? 0 });
  }
}

async function authMiddleware(
  req: NextApiRequest,
  res: NextApiResponse<any>,
  next: NextHandler) {
  const s = await getServerSession({ req });

  if (!s) {
    if (!res.headersSent) {
      return res.status(401).json({ error: 'Unauthorized', code: 0 });
    }
  }

  return next();
}

export function handler(
  {
    options,
    auth = true,
    onError = defaultOnError,
  }: {
    options?: Options<NextApiRequest, NextApiResponse>
    auth?: boolean,
    onError?: typeof defaultOnError
  } = {}
) {
  let h = nextConnect<NextApiRequest, NextApiResponse>({
    onError,
    ...options,
  }).use(Cors(corsOptions));

  if (auth) {
    h = h.use(authMiddleware);
  }

  return h
}

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
});

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
  >['dataType']
>(
  action: K,
  variables?: V,
  options?: FetchQueryOptions<R | null>,
  config?: RequestInit
): Promise<R | null> {
  const key = [action.toString(), variables];

  let endpoint = action.toString();

  let params: Partial<V> = variables;

  let method: RequestInit['method'] = 'GET';
  let data: Record<string, any> = undefined;

  switch (action as unknown as MomoType) {
    case MomoType.SAME_MACHINE: {
      endpoint = '/api/server/momo';
      method = 'POST';
      data = { action, ...variables };
      params = {};
      break;
    }
  }

  const headers = { ...config?.headers };

  if (data) {
    headers['Content-Type'] = 'application/json';
  }

  const url = urlstring(HPX_DOMAIN_URL + endpoint, params as any);

  const cfg: RequestInit = {
    method,
    body: JSON.stringify(data),
    ...config,
    headers,
  };

  return serverQueryClient.fetchQuery(
    key,
    ({ signal }): Promise<R | null> => {
      return fetch(url, cfg).then(async (response) => {
        const is_json = response.headers
          .get('content-type')
          ?.includes('application/json');
        const data = is_json ? await response.json() : null;

        if (!response.ok) {
          const error = (data && data.error) || response.status;
          throw Error(error);
        }
        return data;
      });
    },
    options
  );
}

export const nextAuthOptions: NextAuthOptions = {
  secret: HPX_SECRET,
  // Configure one or more authentication providers
  logger: {
    error(code, metadata) {
      global.app.log.e(code, metadata);
    },
    warn(code) {
      global.app.log.w(code);
    },
    debug(code, metadata) {
      global.app.log.d(code, metadata);
    },
  },
  providers: [
    CredentialsProvider({
      // The name to display on the sign in form (e.g. 'Sign in with...')
      name: 'Happy Panda X',
      id: 'happypandax',
      type: 'credentials',
      // The credentials is used to generate a suitable form on the sign in page.
      // You can specify whatever fields you are expecting to be submitted.
      // e.g. domain, username, password, 2FA token, etc.
      // You can pass any HTML attribute to the <input> tag through the object.
      credentials: {
        username: { label: 'username', type: 'text' },
        password: { label: 'password', type: 'password' },
        host: { label: 'host', type: 'text' },
        port: { label: 'port', type: 'text' },
      },
      async authorize(credentials, req) {
        // You need to provide your own logic here that takes the credentials
        // submitted and returns either a object representing a user or value
        // that is false/null if the credentials are invalid.
        // e.g. return { id: 1, name: 'J Smith', email: 'jsmith@example.com' }
        // You can also use the `req` object to obtain additional parameters
        // (i.e., the request IP address)

        const server = global.app.service.get(ServiceType.Server);

        let host = credentials?.host;
        let port = credentials?.port ? parseInt(credentials?.port) : undefined;

        if (DISABLE_SERVER_CONNECT) {
          host = HPX_SERVER_HOST;
          port = HPX_SERVER_PORT;
        }


        if (host && port) {
          await server.connect({ host, port }).catch((e: ServerError) => {
            global.app.log.e(e);
            if (e instanceof ConnectionError) {
              throw new Error(LOGIN_ERROR.ServerNotConnected);
            } else {
              throw new Error(e?.message);
            }
          });
        }

        const r = await server
          .login(credentials?.username, credentials?.password)
          .catch((e: ServerError) => {
            if (e instanceof AuthWrongCredentialsError) {
              throw new Error(LOGIN_ERROR.InvalidCredentials);
            } else if (e instanceof ConnectionError) {
              throw new Error(LOGIN_ERROR.ServerNotConnected);
            } else {
              global.app.log.e(e);
              throw new Error(e?.message);
            }
          });

        if (!r) {
          throw new Error(LOGIN_ERROR.InvalidCredentials);
        }

        return {
          id: r,
        };
      },
    }),
  ],
  session: {
    strategy: 'jwt' as const,
    maxAge: 30 * 24 * 60 * 60, // 30 days,
  },
  pages: {
    signIn: '/',
    signOut: '/',
    error: '/error', // Error code passed in query string as ?error=
    verifyRequest: '/',
    newUser: '/',
  },
  callbacks: {
    async signIn({ user, account, profile, email, credentials }) {
      return true;
    },
    async redirect({ url, baseUrl }) {
      return HPX_DOMAIN_URL;
    },
    async session({ session, token, user }) {
      return session;
    },
    async jwt({ token, user, account, profile, isNewUser }) {
      return { id: account.providerAccountId };
    },
  },
  events: {
    async signOut(message) {
      const server = global.app.service.get(ServiceType.Server);
      const token = message.token as { id: string };
      await server.logout(token.id);
    },
  },
};

export async function getServerSession({
  req,
}: {
  req?:
  | (IncomingMessage & {
    cookies: Partial<{ [key: string]: string }>;
  })
  | NextApiRequest;
}) {
  const s = await getToken({ req, secret: HPX_SECRET });
  return s as { id: string };
}

export type GetServerSession = typeof getServerSession;
