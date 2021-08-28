import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import {
  InitialDataFunction,
  QueryClient,
  QueryFunctionContext,
  useInfiniteQuery,
  UseInfiniteQueryOptions,
  UseInfiniteQueryResult,
  useMutation,
  UseMutationOptions,
  UseMutationResult,
  useQuery,
  UseQueryOptions,
  UseQueryResult,
} from 'react-query';

import { FieldPath, ServerSortIndex } from '../misc/types';
import { urlstring } from '../misc/utility';

import type ServerService from '../services/server';
export enum QueryType {
  PROFILE = 1,
  PAGES,
  LIBRARY,
  ITEMS,
  ITEM,
  RELATED_ITEMS,
  SIMILAR,
  SEARCH_ITEMS,
  SORT_INDEXES,
  SERVER_STATUS,
}

export enum MutatationType {
  LOGIN = 50,
  UPDATE_GALLERY,
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime:
        process.env.NODE_ENV === 'development' ? Infinity : 1000 * 60 * 60 * 6,
    },
  },
});

export function useMutationType<
  T extends MutationActions,
  K extends T['type'],
  V extends Extract<T, { type: K }>['variables'],
  R extends Extract<T, { type: K }>['dataType'],
  D extends AxiosResponse<R>,
  E extends AxiosError<D>,
  TContext = unknown
>(
  type: K,
  options?: UseMutationOptions<D, E, V, TContext>
): UseMutationResult<D, E, V, TContext> {
  const key = [type.toString()];

  switch (type) {
    case MutatationType.LOGIN: {
      return useMutation(
        key,
        (data) => {
          return axios.post('/api/login', data);
        },
        options
      );
    }

    case MutatationType.UPDATE_GALLERY: {
      return useMutation(
        key,
        (data) => {
          return axios.put('/api/gallery', data);
        },
        options
      );
    }

    default:
      throw Error('Invalid query type');
  }
}

type Falsy = false | undefined;
const isTruthy = <T>(x: T | Falsy): x is T => !!x;

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
  E extends AxiosError<D> = AxiosError<D>,
  I extends Falsy | true = undefined
>(
  type: K,
  variables?: V,
  options?: {
    initialData?: R | InitialDataFunction<R>;
    onQueryKey?: () => any;
    infinite?: I;
    infinitePageParam: I extends Falsy
      ? undefined
      : (variables: V, context: QueryFunctionContext) => V;
  } & (I extends Falsy
    ? Omit<UseQueryOptions<D, E>, 'initialData'>
    : Omit<UseInfiniteQueryOptions<D, E>, 'initialData'>)
): I extends Falsy ? UseQueryResult<D, E> : UseInfiniteQueryResult<D, E> {
  const iData = () => ({
    data:
      typeof options.initialData === 'function'
        ? (options.initialData as InitialDataFunction<R>)()
        : options.initialData,
    status: 200,
    statusText: 'OK',
    headers: {},
    config: {},
    request: {},
  });

  const opts = {
    ...options,
    initialData: options?.initialData
      ? options.infinite
        ? { pages: [iData()], pageParams: [] }
        : iData()
      : undefined,
  };

  const key = [options?.onQueryKey?.() ?? type.toString(), variables];
  let endpoint = '';

  switch (type) {
    case QueryType.SERVER_STATUS: {
      endpoint = '/api/status';
      break;
    }

    case QueryType.SORT_INDEXES: {
      endpoint = '/api/sort_indexes';
      break;
    }

    case QueryType.ITEM: {
      endpoint = '/api/item';
      break;
    }

    case QueryType.ITEMS: {
      endpoint = '/api/items';
      break;
    }

    case QueryType.LIBRARY: {
      endpoint = '/api/library';
      break;
    }

    case QueryType.RELATED_ITEMS: {
      endpoint = '/api/related_items';
      break;
    }

    case QueryType.PAGES: {
      endpoint = '/api/pages';
      break;
    }

    case QueryType.SIMILAR: {
      endpoint = '/api/similar';
      break;
    }

    case QueryType.SEARCH_ITEMS: {
      endpoint = '/api/search_items';
      break;
    }

    default:
      throw Error('Invalid query type');
  }

  if (opts.infinite) {
    return useInfiniteQuery(
      key,
      (ctx) => {
        return axios.get(
          urlstring(endpoint, options.infinitePageParam(variables, ctx))
        );
      },
      opts
    );
  } else {
    return useQuery(
      key,
      () => {
        return axios.get(urlstring(endpoint, variables));
      },
      opts
    );
  }
}

// ======================== ACTIONS ====================================

interface Action {
  variables?: Record<string, any>;
  dataType?: unknown;
}

// ======================== QUERY ACTIONS ====================================

interface QueryAction<T = undefined> extends Action {
  type: QueryType;
}

interface FetchServerStatus<T = undefined> extends QueryAction<T> {
  type: QueryType.SERVER_STATUS;
  dataType: {
    loggedIn: boolean;
    connected: boolean;
  };
}

interface FetchSortIndexes<T = undefined> extends QueryAction<T> {
  type: QueryType.SORT_INDEXES;
  dataType: ServerSortIndex[];
  variables: Parameters<typeof ServerService['prototype']['sort_indexes']>[0];
}

interface FetchProfile<T = undefined> extends QueryAction<T> {
  type: QueryType.PROFILE;
  dataType: Unwrap<ReturnType<ServerService['profile']>>;
  variables: Parameters<ServerService['profile']>[0];
}

interface FetchItem<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEM;
  dataType: Record<string, any>;
  variables: Omit<Parameters<ServerService['item']>[0], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchItems<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEMS;
  dataType: Unwrap<ReturnType<ServerService['items']>>;
  variables: Omit<
    Parameters<typeof ServerService['prototype']['items']>[0],
    'fields'
  > & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchLibrary<T = undefined> extends QueryAction<T> {
  type: QueryType.LIBRARY;
  dataType: Unwrap<ReturnType<ServerService['library']>>;
  variables: Omit<Parameters<ServerService['library']>[0], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchRelatedItems<T = undefined> extends QueryAction<T> {
  type: QueryType.RELATED_ITEMS;
  dataType: Unwrap<ReturnType<ServerService['related_items']>>;
  variables: Omit<Parameters<ServerService['related_items']>[0], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchPages<T = undefined> extends QueryAction<T> {
  type: QueryType.PAGES;
  dataType: Unwrap<ReturnType<ServerService['pages']>>;
  variables: Omit<Parameters<ServerService['pages']>[0], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSimilar<T = undefined> extends QueryAction<T> {
  type: QueryType.SIMILAR;
  dataType: Unwrap<ReturnType<ServerService['similar']>>;
  variables: Omit<Parameters<ServerService['similar']>[0], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSearchItems<T = undefined> extends QueryAction<T> {
  type: QueryType.SEARCH_ITEMS;
  dataType: Unwrap<ReturnType<ServerService['search_items']>>;
  variables: Parameters<ServerService['search_items']>[0];
}

type QueryActions<T = undefined> =
  | FetchProfile<T>
  | FetchItem<T>
  | FetchItems<T>
  | FetchLibrary<T>
  | FetchPages<T>
  | FetchRelatedItems<T>
  | FetchSortIndexes<T>
  | FetchSimilar<T>
  | FetchSearchItems<T>
  | FetchServerStatus<T>;

// ======================== MUTATION ACTIONS ====================================

interface MutationAction extends Action {
  type: MutatationType;
}

interface LoginAction extends MutationAction {
  type: MutatationType.LOGIN;
  variables: {
    username: string;
    password?: string;
    endpoint?: { host: string; port: number };
  };
}

interface UpdateGallery extends MutationAction {
  type: MutatationType.UPDATE_GALLERY;
  variables: { test: string };
}

type MutationActions = LoginAction | UpdateGallery;

// ======================== NORMAL QUERY ====================================

type Actions<T = undefined> = MutationActions | QueryActions<T>;

export class Query {
  static get<
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
  >(action: K, variables?: V, config?: Parameters<AxiosInstance['get']>[1]) {
    const key = [action.toString(), variables];

    switch (action) {
      case QueryType.ITEM: {
        return queryClient.fetchQuery(key, () =>
          axios.get<R>(urlstring('/api/item', variables as any))
        );
      }
      case QueryType.PROFILE: {
        return queryClient.fetchQuery(key, () =>
          axios.get<R>(urlstring('/api/profile', variables as any))
        );
      }
      case QueryType.PAGES: {
        return queryClient.fetchQuery(key, () =>
          axios.get<R>(urlstring('/api/pages', variables as any))
        );
      }
      case QueryType.SEARCH_ITEMS: {
        return queryClient.fetchQuery(key, () =>
          axios.get<R>(urlstring('/api/search_items', variables as any))
        );
      }

      default:
        throw Error('Invalid action type');
    }
  }
}
