import axios, {
  AxiosError,
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
} from 'axios';
import {
  InitialDataFunction,
  MutationObserver,
  MutationObserverOptions,
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
  QUEUE_ITEMS,
  QUEUE_STATE,
  SORT_INDEXES,
  DOWNLOAD_INFO,
  METADATA_INFO,
  SERVER_STATUS,
  LOG,
}

export enum MutatationType {
  LOGIN = 50,
  UPDATE_GALLERY,
  STOP_QUEUE,
  START_QUEUE,
  CLEAR_QUEUE,
  ADD_ITEM_TO_QUEUE,
  REMOVE_ITEM_FROM_QUEUE,
  ADD_ITEMS_TO_METADATA_QUEUE,
  ADD_URLS_TO_DOWNLOAD_QUEUE,
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

  let endpoint = '';
  let method: AxiosRequestConfig['method'] = 'POST';

  switch (type) {
    case MutatationType.LOGIN: {
      endpoint = '/api/login';
      break;
    }

    case MutatationType.UPDATE_GALLERY: {
      endpoint = '/api/gallery';
      break;
    }

    case MutatationType.START_QUEUE: {
      endpoint = '/api/start_queue';
      break;
    }

    case MutatationType.STOP_QUEUE: {
      endpoint = '/api/stop_queue';
      break;
    }

    case MutatationType.CLEAR_QUEUE: {
      endpoint = '/api/clear_queue';
      break;
    }

    case MutatationType.ADD_ITEMS_TO_METADATA_QUEUE: {
      endpoint = '/api/add_items_to_metadata_queue';
      break;
    }

    case MutatationType.ADD_URLS_TO_DOWNLOAD_QUEUE: {
      endpoint = '/api/add_urls_to_download_queue';
      break;
    }

    case MutatationType.ADD_ITEM_TO_QUEUE: {
      endpoint = '/api/add_item_to_queue';
      break;
    }

    case MutatationType.REMOVE_ITEM_FROM_QUEUE: {
      endpoint = '/api/remove_item_from_queue';
      break;
    }

    default:
      throw Error('Invalid mutation type');
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
    infinitePageParam?: I extends Falsy
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

    case QueryType.QUEUE_ITEMS: {
      endpoint = '/api/queue_items';
      break;
    }

    case QueryType.QUEUE_STATE: {
      endpoint = '/api/queue_state';
      break;
    }

    case QueryType.LOG: {
      endpoint = '/api/log';
      break;
    }

    case QueryType.DOWNLOAD_INFO: {
      endpoint = '/api/download_info';
      break;
    }

    case QueryType.METADATA_INFO: {
      endpoint = '/api/metadata_info';
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

interface FetchQueueItems<T = undefined> extends QueryAction<T> {
  type: QueryType.QUEUE_ITEMS;
  dataType: Unwrap<ReturnType<ServerService['queue_items']>>;
  variables: Parameters<ServerService['queue_items']>[0];
}
interface FetchQueueState<T = undefined> extends QueryAction<T> {
  type: QueryType.QUEUE_STATE;
  dataType: Unwrap<ReturnType<ServerService['queue_state']>>;
  variables: Parameters<ServerService['queue_state']>[0];
}

interface FetchLog<T = undefined> extends QueryAction<T> {
  type: QueryType.LOG;
  dataType: Unwrap<ReturnType<ServerService['log']>>;
  variables: Parameters<ServerService['log']>[0];
}

interface FetchDownloadInfo<T = undefined> extends QueryAction<T> {
  type: QueryType.DOWNLOAD_INFO;
  dataType: Unwrap<ReturnType<ServerService['download_info']>>;
  variables: Parameters<ServerService['download_info']>[0];
}

interface FetchMetadataInfo<T = undefined> extends QueryAction<T> {
  type: QueryType.METADATA_INFO;
  dataType: Unwrap<ReturnType<ServerService['metadata_info']>>;
  variables: Parameters<ServerService['metadata_info']>[0];
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
  | FetchQueueItems<T>
  | FetchQueueState<T>
  | FetchLog<T>
  | FetchDownloadInfo<T>
  | FetchMetadataInfo<T>
  | FetchServerStatus<T>;

// ======================== MUTATION ACTIONS ====================================

interface MutationAction<T = undefined> extends Action {
  type: MutatationType;
}

interface LoginAction<T = undefined> extends MutationAction<T> {
  type: MutatationType.LOGIN;
  dataType: Unwrap<ReturnType<ServerService['login']>>;
  variables: {
    username: string;
    password?: string;
    endpoint?: { host: string; port: number };
  };
}

interface UpdateGallery<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_GALLERY;
  dataType: Unwrap<ReturnType<ServerService['login']>>;
  variables: { test: string };
}

interface StopQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.STOP_QUEUE;
  dataType: Unwrap<ReturnType<ServerService['stop_queue']>>;
  variables: Parameters<ServerService['stop_queue']>[0];
}

interface StartQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.START_QUEUE;
  dataType: Unwrap<ReturnType<ServerService['start_queue']>>;
  variables: Parameters<ServerService['start_queue']>[0];
}

interface ClearQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.CLEAR_QUEUE;
  dataType: Unwrap<ReturnType<ServerService['clear_queue']>>;
  variables: Parameters<ServerService['clear_queue']>[0];
}

interface AddItemToQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_ITEM_TO_QUEUE;
  dataType: Unwrap<ReturnType<ServerService['add_item_to_queue']>>;
  variables: Parameters<ServerService['add_item_to_queue']>[0];
}

interface RemoveItemFromQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.REMOVE_ITEM_FROM_QUEUE;
  dataType: Unwrap<ReturnType<ServerService['remove_item_from_queue']>>;
  variables: Parameters<ServerService['remove_item_from_queue']>[0];
}

interface AddItemsToMetadataQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_ITEMS_TO_METADATA_QUEUE;
  dataType: Unwrap<ReturnType<ServerService['add_items_to_metadata_queue']>>;
  variables: Parameters<ServerService['add_items_to_metadata_queue']>[0];
}

interface AddUrlsToDownloadQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_URLS_TO_DOWNLOAD_QUEUE;
  dataType: Unwrap<ReturnType<ServerService['add_urls_to_download_queue']>>;
  variables: Parameters<ServerService['add_urls_to_download_queue']>[0];
}

type MutationActions<T = undefined> =
  | LoginAction<T>
  | UpdateGallery<T>
  | AddItemToQueue<T>
  | RemoveItemFromQueue<T>
  | AddItemsToMetadataQueue<T>
  | AddUrlsToDownloadQueue<T>
  | StopQueue<T>
  | StartQueue<T>
  | ClearQueue<T>;

// ======================== NORMAL QUERY ====================================

type Actions<T = undefined> = MutationActions<T> | QueryActions<T>;

export class Query {
  static mutationObservers: Record<
    string,
    MutationObserver<any, any, any, any>
  >;

  static get<
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
        throw Error('Invalid query type');
    }
  }

  static post<
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
    E extends AxiosError<R> = AxiosError<R>
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
    let obs: MutationObserver<AxiosResponse<R>, E, V> =
      Query.mutationObservers[key];
    if (!obs) {
      let endpoint = '';

      switch (action) {
        case MutatationType.ADD_ITEM_TO_QUEUE: {
          endpoint = '/api/item';
          break;
        }

        default:
          throw Error('Invalid mutation type');
      }

      const fn = (v: V) => axios.post<R>(urlstring(endpoint), v, reqConfig);

      obs = new MutationObserver<AxiosResponse<R>, E, V>(queryClient, {
        ...options,
        mutationKey: key,
        mutationFn: fn,
      });

      Query.mutationObservers[key] = obs;
    }

    return obs.mutate(variables);
  }
}
