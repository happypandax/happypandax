import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
} from 'axios';

import {
  FetchQueryOptions,
  InitialDataFunction,
  MutationObserver,
  MutationObserverOptions,
  PlaceholderDataFunction,
  QueryClient,
  QueryFunctionContext,
  QueryKey,
  useInfiniteQuery,
  UseInfiniteQueryOptions,
  UseInfiniteQueryResult,
  useMutation,
  UseMutationOptions,
  UseMutationResult,
  useQuery,
  UseQueryOptions,
  UseQueryResult,
} from '@tanstack/react-query';

import {
  MutatationType,
  MutationActions,
  QueryActions,
  QueryType,
} from '../misc/query';
import { pauseUntil, urlstring } from '../misc/utility';
import {
  GlobalState,
  onGlobalStateChange,
  useGlobalValue,
} from '../state/global';

import type { ErrorResponseData } from '../misc/requests';

export { QueryType, MutatationType } from '../misc/query'

export const queryClient = new QueryClient({
  defaultOptions: {
    mutations: {
      networkMode: 'offlineFirst',
      retry: () => false,
      // https://tanstack.com/query/v4/docs/guides/migrating-to-react-query-4#no-default-manual-garbage-collection-server-side
      cacheTime: typeof window === 'undefined' ? Infinity : undefined,
    },
    queries: {
      networkMode: 'offlineFirst',
      retry: () => false,
      // https://tanstack.com/query/v4/docs/guides/migrating-to-react-query-4#no-default-manual-garbage-collection-server-side
      cacheTime: typeof window === 'undefined' ? Infinity : undefined,
      staleTime:
        process.env.NODE_ENV === 'development' ? Infinity : 1000 * 60 * 60 * 1, // 1 hours
    },
  },
});

const defaultClientOptions = queryClient.getDefaultOptions();

onGlobalStateChange(['connected', 'loggedIn'], (state) => {
  if (!state.connected || !state.loggedIn) {
    queryClient.cancelQueries();
    queryClient.setDefaultOptions({
      mutations: {
        retry: () => false,
      },
      queries: {
        retry: () => false,
        enabled: false,
      },
    });
  } else {
    queryClient.setDefaultOptions({
      mutations: {
        retry: defaultClientOptions.mutations.retry || true,
      },
      queries: {
        retry: defaultClientOptions.queries.retry || true,
        enabled: defaultClientOptions.queries.enabled || true,
      },
    });
  }
});

queryClient.setDefaultOptions({});

export function useMutationType<
  T extends MutationActions,
  K extends T['type'],
  V extends Extract<T, { type: K }>['variables'],
  R extends Extract<T, { type: K }>['dataType'],
  D extends AxiosResponse<R>,
  E extends AxiosError<ErrorResponseData>,
  TContext = unknown
>(
  type: K,
  options?: UseMutationOptions<D, E, V, TContext>
): UseMutationResult<D, E, V, TContext> {
  const key = [type.toString()];

  let endpoint = type as string;
  let method: AxiosRequestConfig['method'] = 'POST';

  switch (type) {

    case MutatationType.INSTALL_PLUGIN: {
      method = 'POST';
      break;
    }

    case MutatationType.DISABLE_PLUGIN: {
      method = 'PUT';
      break;
    }

    case MutatationType.REMOVE_PLUGIN: {
      method = 'DELETE';
      break;
    }

  }

  return useMutation(
    key,
    (data) => {
      return axios.request({
        method,
        url: endpoint,
        data,
      });
    },
    options
  );
}

type Falsy = false | undefined;

export function CreateInitialData<R>(d: R | InitialDataFunction<R>) {
  return {
    data: typeof d === 'function' ? (d as InitialDataFunction<R>)() : d,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {},
    request: {},
  };
}

export function getQueryTypeKey(
  type: any,
  variables?: any,
  onQueryKey?: () => any
) {
  return [onQueryKey?.() ?? type.toString(), variables];
}

// If A is defined, it renders the rest of generics useless
// see https://github.com/microsoft/TypeScript/issues/26242
// and https://github.com/microsoft/TypeScript/issues/10571
export function useQueryType<
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
  >['dataType'],
  D extends AxiosResponse<R> = AxiosResponse<R>,
  E extends AxiosError<ErrorResponseData> = AxiosError<ErrorResponseData>,
  I extends Falsy | true = undefined
>(
  type: K,
  variables?: V,
  options?: {
    initialData?: R | InitialDataFunction<R>;
    placeholderData?: R | PlaceholderDataFunction<R>;
    onQueryKey?: () => any;
    infinite?: I;
    infinitePageParam?: I extends Falsy
    ? undefined
    : (variables: V, context: QueryFunctionContext) => V;
  } & (I extends Falsy
    ? Omit<UseQueryOptions<D, E>, 'initialData' | 'placeholderData'>
    : Omit<UseInfiniteQueryOptions<D, E>, 'initialData' | 'placeholderData'>)
): (I extends Falsy ? UseQueryResult<D, E> : UseInfiniteQueryResult<D, E>) & {
  queryKey: QueryKey;
} {
  const opts = {
    ...options,
    initialData: options?.initialData
      ? options.infinite
        ? { pages: [CreateInitialData(options.initialData)], pageParams: [] }
        : CreateInitialData(options.initialData)
      : undefined,
    placeholderData: options?.placeholderData
      ? options.infinite
        ? {
          pages: [CreateInitialData(options.placeholderData)],
          pageParams: [],
        }
        : CreateInitialData(options.placeholderData)
      : undefined,
  };

  const key = getQueryTypeKey(type, variables, options?.onQueryKey);

  const connected = useGlobalValue('connected');
  const loggedIn = useGlobalValue('loggedIn');

  if (!connected || !loggedIn) {
    opts.enabled = false;
    global.log.d(
      'Query disabled because of not connected or not logged in',
      key
    );
  }

  let endpoint = type as string;
  let method: AxiosRequestConfig['method'] = 'GET';

  switch (type) {

    case QueryType.QUEUE_ITEMS:
    case QueryType.LOG:
    case QueryType.CONFIG:
    case QueryType.COMMAND_PROGRESS: {
      if (opts.cacheTime === undefined) {
        opts.cacheTime = 0;
      }
      break;
    }

    case QueryType.COMMAND_STATE:
    case QueryType.COMMAND_VALUE:
    case QueryType.ACTIVITIES: {
      throw Error('Not implemented');
    }

  }

  let r;

  if (opts.infinite) {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    r = useInfiniteQuery(
      key,
      (ctx) => {
        return axios.request({
          method,
          url: urlstring(
            endpoint,
            options.infinitePageParam(variables, ctx) as any
          ),
          signal: ctx.signal,
        });
      },
      opts
    );
  } else {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    r = useQuery(
      key,
      ({ signal }) => {
        return axios.request({
          method,
          url: urlstring(endpoint, variables as any),
          signal,
        });
      },
      opts
    );
  }

  return { ...r, queryKey: key };
}


// ======================== NORMAL QUERY ====================================


export class Query {
  static mutationObservers: Record<
    string,
    MutationObserver<any, any, any, any>
  > = {};

  static async fetch<
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
    >['dataType']
  >(
    action: K,
    variables?: V,
    options?: FetchQueryOptions<AxiosResponse<R, any>>,
    config?: Parameters<AxiosInstance['get']>[1]
  ) {
    const key = [action.toString(), variables];

    if (!GlobalState.connected || !GlobalState.loggedIn) {
      // pause until connected

      await pauseUntil(
        () => GlobalState.connected && GlobalState.loggedIn,
        1000,
        1000 * 60 * 60 * 6
      );
    }

    switch (action) {
      case QueryType.ITEM: {
        return queryClient.fetchQuery(
          key,
          ({ signal }) =>
            axios.get<R>(urlstring('/api/item', variables as any), { signal }),
          options
        );
      }
      case QueryType.PROFILE: {
        return queryClient.fetchQuery(
          key,
          ({ signal }) =>
            axios.get<R>(urlstring('/api/profile', variables as any), {
              signal,
            }),
          options
        );
      }
      case QueryType.PAGES: {
        return queryClient.fetchQuery(
          key,
          ({ signal }) =>
            axios.get<R>(urlstring('/api/pages', variables as any), { signal }),
          options
        );
      }
      case QueryType.SEARCH_LABELS: {
        return queryClient.fetchQuery(
          key,
          ({ signal }) =>
            axios.get<R>(urlstring('/api/search_labels', variables as any), {
              signal,
            }),
          options
        );
      }
      case QueryType.SEARCH_ITEMS: {
        return queryClient.fetchQuery(
          key,
          ({ signal }) =>
            axios.get<R>(urlstring('/api/search_items', variables as any), {
              signal,
            }),
          options
        );
      }
      case QueryType.ACTIVITIES: {
        return queryClient.fetchQuery(
          key,
          ({ signal }) =>
            axios.post<R>(urlstring('/api/activities'), variables, { signal }),
          options
        );
      }
      case QueryType.COMMAND_STATE: {
        return queryClient.fetchQuery(
          key,
          ({ signal }) =>
            axios.post<R>(urlstring('/api/command_state'), variables, {
              signal,
            }),
          options
        );
      }
      case QueryType.COMMAND_VALUE: {
        return queryClient.fetchQuery(
          key,
          ({ signal }) =>
            axios.post<R>(urlstring('/api/command_value'), variables, {
              signal,
            }),
          options
        );
      }

      default:
        throw Error('Invalid query type');
    }
  }

  static async mutate<
    A = undefined,
    T extends MutationActions<A> = MutationActions<A>,
    K extends T['type'] = T['type'],
    V extends Extract<T, { type: K }>['variables'] = Extract<
      T,
      { type: K }
    >['variables'],
    R extends Extract<T, { type: K }>['dataType'] = Extract<
      T,
      { type: K }
    >['dataType'],
    E extends AxiosError<ErrorResponseData> = AxiosError<ErrorResponseData>
  >(
    action: K,
    variables: V,
    options?: Omit<
      MutationObserverOptions<AxiosResponse<R>, E, V>,
      'mutationFn' | 'mutationKey' | 'variables'
    >,
    reqConfig?: Parameters<AxiosInstance['post']>[2]
  ) {
    const key = JSON.stringify([action.toString(), variables]);

    if (!GlobalState.connected || !GlobalState.loggedIn) {
      // pause until connected

      await pauseUntil(
        () => GlobalState.connected && GlobalState.loggedIn,
        1000,
        1000 * 60 * 60 * 6
      );
    }

    let obs: MutationObserver<AxiosResponse<R>, E, V> =
      Query.mutationObservers[key];
    if (!obs) {
      let endpoint = action as string;

      const fn = (v: V) => axios.post<R>(urlstring(endpoint), v, reqConfig);

      obs = new MutationObserver<AxiosResponse<R>, E, V>(queryClient, {
        mutationKey: [key],
        mutationFn: fn,
      });

      Query.mutationObservers[key] = obs;
    }

    return obs.mutate(variables, options);
  }
}
