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
}

export const queryClient = new QueryClient({
  defaultOptions: {
    mutations: {
      networkMode: 'offlineFirst',
      retry: true,
      // https://tanstack.com/query/v4/docs/guides/migrating-to-react-query-4#no-default-manual-garbage-collection-server-side
      cacheTime: typeof window === 'undefined' ? Infinity : undefined,
    },
    queries: {
      networkMode: 'offlineFirst',
      retry: true,
      // https://tanstack.com/query/v4/docs/guides/migrating-to-react-query-4#no-default-manual-garbage-collection-server-side
      cacheTime: typeof window === 'undefined' ? Infinity : undefined,
      staleTime:
        process.env.NODE_ENV === 'development' ? Infinity : 1000 * 60 * 60 * 3, // 3 hours
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
  E extends AxiosError<D> = AxiosError<D>,
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
  variables: Omit<Parameters<ServerService['items']>[0], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSearchItems<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEMS;
  dataType: Unwrap<ReturnType<ServerService['search_items']>>;
  variables: Omit<Parameters<ServerService['search_items']>[0], 'fields'> & {
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

interface FetchSearchLabels<T = undefined> extends QueryAction<T> {
  type: QueryType.SEARCH_LABELS;
  dataType: Unwrap<ReturnType<ServerService['search_labels']>>;
  variables: Parameters<ServerService['search_labels']>[0];
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

interface FetchConfig<T = undefined> extends QueryAction<T> {
  type: QueryType.CONFIG;
  dataType: Unwrap<ReturnType<ServerService['config']>>;
  variables: Parameters<ServerService['config']>[0];
}

interface FetchPlugin<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGIN;
  dataType: Unwrap<ReturnType<ServerService['plugin']>>;
  variables: Parameters<ServerService['plugin']>[0];
}

interface FetchPluginUpdate<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGIN_UPDATE;
  dataType: Unwrap<ReturnType<ServerService['check_plugin_update']>>;
  variables: Parameters<ServerService['check_plugin_update']>[0];
}

interface FetchPlugins<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGINS;
  dataType: Unwrap<ReturnType<ServerService['list_plugins']>>;
  variables: Parameters<ServerService['list_plugins']>[0];
}

interface FetchCommandProgress<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_PROGRESS;
  dataType: Unwrap<ReturnType<ServerService['command_progress']>>;
  variables: Parameters<ServerService['command_progress']>[0];
}

interface FetchCommandState<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_STATE;
  dataType: Unwrap<ReturnType<ServerService['command_state']>>;
  variables: Parameters<ServerService['command_state']>[0];
}

interface FetchCommandValue<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_VALUE;
  dataType: Unwrap<ReturnType<ServerService['command_value']>>;
  variables: Parameters<ServerService['command_value']>[0];
}
interface FetchActivities<T = undefined> extends QueryAction<T> {
  type: QueryType.ACTIVITIES;
  dataType: Unwrap<ReturnType<ServerService['activities']>>;
  variables: Parameters<ServerService['activities']>[0];
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
  dataType: Unwrap<ReturnType<ServerService['login']>>;
  variables: {
    username: string;
    password?: string;
    endpoint?: { host: string; port: number };
  };
}

interface UpdateItem<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_ITEM;
  dataType: Unwrap<ReturnType<ServerService['update_item']>>;
  variables: Parameters<ServerService['update_item']>[0];
}

interface UpdateMetatags<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_METATAGS;
  dataType: Unwrap<ReturnType<ServerService['update_metatags']>>;
  variables: Parameters<ServerService['update_metatags']>[0];
}

interface UpdateConfig<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_CONFIG;
  dataType: Unwrap<ReturnType<ServerService['set_config']>>;
  variables: Parameters<ServerService['set_config']>[0];
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

interface PageReadEvent<T = undefined> extends MutationAction<T> {
  type: MutatationType.PAGE_READ_EVENT;
  dataType: Unwrap<ReturnType<ServerService['page_read_event']>>;
  variables: Parameters<ServerService['page_read_event']>[0];
}

interface InstallPlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.INSTALL_PLUGIN;
  dataType: Unwrap<ReturnType<ServerService['install_plugin']>>;
  variables: Parameters<ServerService['install_plugin']>[0];
}

interface DisablePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.DISABLE_PLUGIN;
  dataType: Unwrap<ReturnType<ServerService['disable_plugin']>>;
  variables: Parameters<ServerService['disable_plugin']>[0];
}

interface RemovePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.REMOVE_PLUGIN;
  dataType: Unwrap<ReturnType<ServerService['remove_plugin']>>;
  variables: Parameters<ServerService['remove_plugin']>[0];
}

interface UpdatePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_CONFIG;
  dataType: Unwrap<ReturnType<ServerService['update_plugin']>>;
  variables: Parameters<ServerService['update_plugin']>[0];
}

interface OpenGallery<T = undefined> extends MutationAction<T> {
  type: MutatationType.OPEN_GALLERY;
  dataType: Unwrap<ReturnType<ServerService['open_gallery']>>;
  variables: Parameters<ServerService['open_gallery']>[0];
}

interface UpdateFilters<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_FILTERS;
  dataType: Unwrap<ReturnType<ServerService['update_filters']>>;
  variables: Parameters<ServerService['update_filters']>[0];
}

interface StartCommand<T = undefined> extends MutationAction<T> {
  type: MutatationType.START_COMMAND;
  dataType: Unwrap<ReturnType<ServerService['start_command']>>;
  variables: Parameters<ServerService['start_command']>[0];
}

interface StopCommand<T = undefined> extends MutationAction<T> {
  type: MutatationType.STOP_COMMAND;
  dataType: Unwrap<ReturnType<ServerService['stop_command']>>;
  variables: Parameters<ServerService['stop_command']>[0];
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
