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
} from 'react-query';

import type { ErrorResponseData, RequestOptions } from '../misc/requests';
import { FieldPath, ServerSortIndex } from '../misc/types';
import { pauseUntil, urlstring } from '../misc/utility';
import type ServerService from '../services/server';
import {
  GlobalState,
  onGlobalStateChange,
  useGlobalValue,
} from '../state/global';

export enum QueryType {
  PROFILE = 1,
  PAGES,
  LIBRARY,
  ITEMS,
  ITEM,
  RELATED_ITEMS,
  SEARCH_ITEMS,
  SIMILAR,
  SEARCH_LABELS,
  QUEUE_ITEMS,
  QUEUE_STATE,
  SORT_INDEXES,
  DOWNLOAD_INFO,
  METADATA_INFO,
  SERVER_STATUS,
  CONFIG,
  LOG,
  PLUGIN,
  PLUGINS,
  PLUGIN_UPDATE,
  COMMAND_STATE,
  COMMAND_VALUE,
  COMMAND_PROGRESS,
  ACTIVITIES,
}

export enum MutatationType {
  LOGIN = 100,
  UPDATE_ITEM,
  UPDATE_METATAGS,
  UPDATE_CONFIG,
  START_COMMAND,
  STOP_COMMAND,
  STOP_QUEUE,
  START_QUEUE,
  CLEAR_QUEUE,
  ADD_ITEM_TO_QUEUE,
  OPEN_GALLERY,
  REMOVE_ITEM_FROM_QUEUE,
  ADD_ITEMS_TO_METADATA_QUEUE,
  ADD_URLS_TO_DOWNLOAD_QUEUE,
  PAGE_READ_EVENT,
  INSTALL_PLUGIN,
  DISABLE_PLUGIN,
  REMOVE_PLUGIN,
  UPDATE_PLUGIN,
  UPDATE_FILTERS,
  RESOLVE_PATH_PATTERN,
}

export const queryClient = new QueryClient({
  defaultOptions: {
    mutations: {
      networkMode: 'offlineFirst',
      retry: false,
      // https://tanstack.com/query/v4/docs/guides/migrating-to-react-query-4#no-default-manual-garbage-collection-server-side
      cacheTime: typeof window === 'undefined' ? Infinity : undefined,
    },
    queries: {
      networkMode: 'offlineFirst',
      retry: 2,
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
        retry: false,
      },
      queries: {
        retry: false,
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

  let endpoint = '';
  let method: AxiosRequestConfig['method'] = 'POST';

  switch (type) {
    case MutatationType.LOGIN: {
      endpoint = '/api/login';
      break;
    }

    case MutatationType.UPDATE_ITEM: {
      endpoint = '/api/item';
      break;
    }

    case MutatationType.UPDATE_METATAGS: {
      endpoint = '/api/metatags';
      break;
    }

    case MutatationType.UPDATE_CONFIG: {
      endpoint = '/api/config';
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

    case MutatationType.PAGE_READ_EVENT: {
      endpoint = '/api/page_read_event';
      break;
    }

    case MutatationType.INSTALL_PLUGIN: {
      endpoint = '/api/plugin';
      method = 'POST';
      break;
    }

    case MutatationType.DISABLE_PLUGIN: {
      endpoint = '/api/plugin';
      method = 'PUT';
      break;
    }

    case MutatationType.REMOVE_PLUGIN: {
      endpoint = '/api/plugin';
      method = 'DELETE';
      break;
    }

    case MutatationType.UPDATE_PLUGIN: {
      endpoint = '/api/plugin_update';
      break;
    }

    case MutatationType.UPDATE_FILTERS: {
      endpoint = '/api/update_filters';
      break;
    }

    case MutatationType.RESOLVE_PATH_PATTERN: {
      endpoint = '/api/resolve_path_pattern';
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

  let endpoint = '';
  let method: AxiosRequestConfig['method'] = 'GET';

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

    case QueryType.SEARCH_LABELS: {
      endpoint = '/api/search_items';
      break;
    }

    case QueryType.QUEUE_ITEMS: {
      endpoint = '/api/queue_items';
      if (opts.cacheTime === undefined) {
        opts.cacheTime = 0;
      }
      break;
    }

    case QueryType.QUEUE_STATE: {
      endpoint = '/api/queue_state';
      break;
    }

    case QueryType.LOG: {
      endpoint = '/api/log';
      if (opts.cacheTime === undefined) {
        opts.cacheTime = 0;
      }
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

    case QueryType.CONFIG: {
      endpoint = '/api/config';
      if (opts.cacheTime === undefined) {
        opts.cacheTime = 0;
      }
      break;
    }

    case QueryType.PLUGINS: {
      endpoint = '/api/plugins';
      break;
    }

    case QueryType.PLUGIN: {
      endpoint = '/api/plugin';
      break;
    }

    case QueryType.PLUGIN_UPDATE: {
      endpoint = '/api/plugin_update';
      break;
    }

    case QueryType.COMMAND_PROGRESS: {
      endpoint = '/api/command_progress';
      if (opts.cacheTime === undefined) {
        opts.cacheTime = 0;
      }
      break;
    }

    case QueryType.COMMAND_STATE:
    case QueryType.COMMAND_VALUE:
    case QueryType.ACTIVITIES: {
      throw Error('Not implemented');
      break;
    }

    default:
      throw Error('Invalid query type');
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

// ======================== ACTIONS ====================================

type ServiceParameters = {
  [K in keyof ServerService]:
    | {
        __options?: RequestOptions;
      }
    | Parameters<
        ServerService[K] extends (...args: any[]) => any
          ? ServerService[K]
          : never
      >[0];
};

type ServiceReturnType = {
  [K in keyof ServerService]: Unwrap<
    ReturnType<
      ServerService[K] extends (...args: any[]) => any
        ? ServerService[K]
        : never
    >
  >;
};

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
  variables: ServiceParameters['sort_indexes'];
}

interface FetchProfile<T = undefined> extends QueryAction<T> {
  type: QueryType.PROFILE;
  dataType: ServiceReturnType['profile'];
  variables: ServiceParameters['profile'];
}

interface FetchItem<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEM;
  dataType: Record<string, any>;
  variables: Omit<ServiceParameters['item'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchItems<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEMS;
  dataType: ServiceReturnType['items'];
  variables: Omit<ServiceParameters['items'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSearchItems<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEMS;
  dataType: ServiceReturnType['search_items'];
  variables: Omit<ServiceParameters['search_items'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchLibrary<T = undefined> extends QueryAction<T> {
  type: QueryType.LIBRARY;
  dataType: ServiceReturnType['library'];
  variables: Omit<ServiceParameters['library'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchRelatedItems<T = undefined> extends QueryAction<T> {
  type: QueryType.RELATED_ITEMS;
  dataType: ServiceReturnType['related_items'];
  variables: Omit<ServiceParameters['related_items'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchPages<T = undefined> extends QueryAction<T> {
  type: QueryType.PAGES;
  dataType: ServiceReturnType['pages'];
  variables: Omit<ServiceParameters['pages'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSimilar<T = undefined> extends QueryAction<T> {
  type: QueryType.SIMILAR;
  dataType: ServiceReturnType['similar'];
  variables: Omit<ServiceParameters['similar'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSearchLabels<T = undefined> extends QueryAction<T> {
  type: QueryType.SEARCH_LABELS;
  dataType: ServiceReturnType['search_labels'];
  variables: ServiceParameters['search_labels'];
}

interface FetchQueueItems<T = undefined> extends QueryAction<T> {
  type: QueryType.QUEUE_ITEMS;
  dataType: ServiceReturnType['queue_items'];
  variables: ServiceParameters['queue_items'];
}
interface FetchQueueState<T = undefined> extends QueryAction<T> {
  type: QueryType.QUEUE_STATE;
  dataType: ServiceReturnType['queue_state'];
  variables: ServiceParameters['queue_state'];
}

interface FetchLog<T = undefined> extends QueryAction<T> {
  type: QueryType.LOG;
  dataType: ServiceReturnType['log'];
  variables: ServiceParameters['log'];
}

interface FetchDownloadInfo<T = undefined> extends QueryAction<T> {
  type: QueryType.DOWNLOAD_INFO;
  dataType: ServiceReturnType['download_info'];
  variables: ServiceParameters['download_info'];
}

interface FetchMetadataInfo<T = undefined> extends QueryAction<T> {
  type: QueryType.METADATA_INFO;
  dataType: ServiceReturnType['metadata_info'];
  variables: ServiceParameters['metadata_info'];
}

interface FetchConfig<T = undefined> extends QueryAction<T> {
  type: QueryType.CONFIG;
  dataType: ServiceReturnType['config'];
  variables: ServiceParameters['config'];
}

interface FetchPlugin<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGIN;
  dataType: ServiceReturnType['plugin'];
  variables: ServiceParameters['plugin'];
}

interface FetchPluginUpdate<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGIN_UPDATE;
  dataType: ServiceReturnType['check_plugin_update'];
  variables: ServiceParameters['check_plugin_update'];
}

interface FetchPlugins<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGINS;
  dataType: ServiceReturnType['list_plugins'];
  variables: ServiceParameters['list_plugins'];
}

interface FetchCommandProgress<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_PROGRESS;
  dataType: ServiceReturnType['command_progress'];
  variables: ServiceParameters['command_progress'];
}

interface FetchCommandState<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_STATE;
  dataType: ServiceReturnType['command_state'];
  variables: ServiceParameters['command_state'];
}

interface FetchCommandValue<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_VALUE;
  dataType: ServiceReturnType['command_value'];
  variables: ServiceParameters['command_value'];
}
interface FetchActivities<T = undefined> extends QueryAction<T> {
  type: QueryType.ACTIVITIES;
  dataType: ServiceReturnType['activities'];
  variables: ServiceParameters['activities'];
}

type QueryActions<T = undefined> =
  | FetchProfile<T>
  | FetchItem<T>
  | FetchItems<T>
  | FetchLibrary<T>
  | FetchPages<T>
  | FetchSearchLabels<T>
  | FetchRelatedItems<T>
  | FetchSortIndexes<T>
  | FetchSimilar<T>
  | FetchSearchItems<T>
  | FetchQueueItems<T>
  | FetchQueueState<T>
  | FetchLog<T>
  | FetchDownloadInfo<T>
  | FetchMetadataInfo<T>
  | FetchConfig<T>
  | FetchPlugin<T>
  | FetchPluginUpdate<T>
  | FetchPlugins<T>
  | FetchCommandProgress<T>
  | FetchCommandState<T>
  | FetchCommandValue<T>
  | FetchActivities<T>
  | FetchServerStatus<T>;

// ======================== MUTATION ACTIONS ====================================

interface MutationAction<T = undefined> extends Action {
  type: MutatationType;
}

interface LoginAction<T = undefined> extends MutationAction<T> {
  type: MutatationType.LOGIN;
  dataType: ServiceReturnType['login'];
  variables: {
    username: string;
    password?: string;
    endpoint?: { host: string; port: number };
  };
}

interface UpdateItem<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_ITEM;
  dataType: ServiceReturnType['update_item'];
  variables: ServiceParameters['update_item'];
}

interface UpdateMetatags<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_METATAGS;
  dataType: ServiceReturnType['update_metatags'];
  variables: ServiceParameters['update_metatags'];
}

interface UpdateConfig<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_CONFIG;
  dataType: ServiceReturnType['set_config'];
  variables: ServiceParameters['set_config'];
}

interface StopQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.STOP_QUEUE;
  dataType: ServiceReturnType['stop_queue'];
  variables: ServiceParameters['stop_queue'];
}

interface StartQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.START_QUEUE;
  dataType: ServiceReturnType['start_queue'];
  variables: ServiceParameters['start_queue'];
}

interface ClearQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.CLEAR_QUEUE;
  dataType: ServiceReturnType['clear_queue'];
  variables: ServiceParameters['clear_queue'];
}

interface AddItemToQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_ITEM_TO_QUEUE;
  dataType: ServiceReturnType['add_item_to_queue'];
  variables: ServiceParameters['add_item_to_queue'];
}

interface RemoveItemFromQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.REMOVE_ITEM_FROM_QUEUE;
  dataType: ServiceReturnType['remove_item_from_queue'];
  variables: ServiceParameters['remove_item_from_queue'];
}

interface AddItemsToMetadataQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_ITEMS_TO_METADATA_QUEUE;
  dataType: ServiceReturnType['add_items_to_metadata_queue'];
  variables: ServiceParameters['add_items_to_metadata_queue'];
}

interface AddUrlsToDownloadQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_URLS_TO_DOWNLOAD_QUEUE;
  dataType: ServiceReturnType['add_urls_to_download_queue'];
  variables: ServiceParameters['add_urls_to_download_queue'];
}

interface PageReadEvent<T = undefined> extends MutationAction<T> {
  type: MutatationType.PAGE_READ_EVENT;
  dataType: ServiceReturnType['page_read_event'];
  variables: ServiceParameters['page_read_event'];
}

interface InstallPlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.INSTALL_PLUGIN;
  dataType: ServiceReturnType['install_plugin'];
  variables: ServiceParameters['install_plugin'];
}

interface DisablePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.DISABLE_PLUGIN;
  dataType: ServiceReturnType['disable_plugin'];
  variables: ServiceParameters['disable_plugin'];
}

interface RemovePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.REMOVE_PLUGIN;
  dataType: ServiceReturnType['remove_plugin'];
  variables: ServiceParameters['remove_plugin'];
}

interface UpdatePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_CONFIG;
  dataType: ServiceReturnType['update_plugin'];
  variables: ServiceParameters['update_plugin'];
}

interface OpenGallery<T = undefined> extends MutationAction<T> {
  type: MutatationType.OPEN_GALLERY;
  dataType: ServiceReturnType['open_gallery'];
  variables: ServiceParameters['open_gallery'];
}

interface UpdateFilters<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_FILTERS;
  dataType: ServiceReturnType['update_filters'];
  variables: ServiceParameters['update_filters'];
}

interface StartCommand<T = undefined> extends MutationAction<T> {
  type: MutatationType.START_COMMAND;
  dataType: ServiceReturnType['start_command'];
  variables: ServiceParameters['start_command'];
}

interface StopCommand<T = undefined> extends MutationAction<T> {
  type: MutatationType.STOP_COMMAND;
  dataType: ServiceReturnType['stop_command'];
  variables: ServiceParameters['stop_command'];
}

interface ResolvePathPattern<T = undefined> extends MutationAction<T> {
  type: MutatationType.RESOLVE_PATH_PATTERN;
  dataType: ServiceReturnType['resolve_path_pattern'];
  variables: ServiceParameters['resolve_path_pattern'];
}

type MutationActions<T = undefined> =
  | LoginAction<T>
  | UpdateItem<T>
  | UpdateMetatags<T>
  | UpdateConfig<T>
  | AddItemToQueue<T>
  | RemoveItemFromQueue<T>
  | AddItemsToMetadataQueue<T>
  | AddUrlsToDownloadQueue<T>
  | PageReadEvent<T>
  | StopQueue<T>
  | StartQueue<T>
  | UpdatePlugin<T>
  | RemovePlugin<T>
  | DisablePlugin<T>
  | InstallPlugin<T>
  | OpenGallery<T>
  | UpdateFilters<T>
  | StartCommand<T>
  | StopCommand<T>
  | ResolvePathPattern<T>
  | ClearQueue<T>;

// ======================== NORMAL QUERY ====================================

type Actions<T = undefined> = MutationActions<T> | QueryActions<T>;

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
      let endpoint = '';

      switch (action) {
        case MutatationType.UPDATE_ITEM: {
          endpoint = '/api/item';
          break;
        }
        case MutatationType.UPDATE_METATAGS: {
          endpoint = '/api/metatags';
          break;
        }
        case MutatationType.START_COMMAND: {
          endpoint = '/api/start_command';
          break;
        }
        case MutatationType.STOP_COMMAND: {
          endpoint = '/api/stop_command';
          break;
        }

        default:
          throw Error('Invalid mutation type');
      }

      const fn = (v: V) => axios.post<R>(urlstring(endpoint), v, reqConfig);

      obs = new MutationObserver<AxiosResponse<R>, E, V>(queryClient, {
        mutationKey: key,
        mutationFn: fn,
      });

      Query.mutationObservers[key] = obs;
    }

    return obs.mutate(variables, options);
  }
}
