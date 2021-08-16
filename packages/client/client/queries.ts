import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import {
  InitialDataFunction,
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
  ITEMS,
  ITEM,
  RELATED_ITEMS,
  SIMILAR,
  SORT_INDEXES,
  SERVER_STATUS,
}

export enum MutatationType {
  LOGIN = 50,
  UPDATE_GALLERY,
}

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
  switch (type) {
    case MutatationType.LOGIN: {
      return useMutation(
        [type.toString()],
        (data) => {
          return axios.post('/api/login', data);
        },
        options
      );
    }

    case MutatationType.UPDATE_GALLERY: {
      return useMutation(
        [type.toString()],
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
  E extends AxiosError<D> = AxiosError<D>
>(
  type: K,
  variables?: V,
  options?: Omit<UseQueryOptions<D, E>, 'initialData'> & {
    initialData?: R | InitialDataFunction<R>;
  }
): UseQueryResult<D, E> {
  const opts = {
    ...options,
    initialData: options?.initialData
      ? {
          data:
            typeof options.initialData === 'function'
              ? (options.initialData as InitialDataFunction<R>)()
              : options.initialData,
          status: 200,
          statusText: 'OK',
          headers: {},
          config: {},
          request: {},
        }
      : undefined,
  };

  switch (type) {
    case QueryType.SERVER_STATUS: {
      return useQuery(
        [type.toString()],
        () => {
          return axios.get(urlstring('/api/status'));
        },
        opts
      );
    }

    case QueryType.SORT_INDEXES: {
      return useQuery(
        [type.toString()],
        () => {
          return axios.get(urlstring('/api/sort_indexes', variables));
        },
        opts
      );
    }

    case QueryType.ITEM: {
      return useQuery(
        [type.toString(), variables],
        () => {
          return axios.get(urlstring('/api/item', variables));
        },
        opts
      );
    }

    case QueryType.ITEMS: {
      return useQuery(
        [type.toString()],
        () => {
          return axios.get(urlstring('/api/items', variables));
        },
        opts
      );
    }

    case QueryType.RELATED_ITEMS: {
      return useQuery(
        [type.toString()],
        () => {
          return axios.get(urlstring('/api/related_items', variables));
        },
        opts
      );
    }

    case QueryType.PAGES: {
      return useQuery(
        [type.toString()],
        () => {
          return axios.get(urlstring('/api/pages', variables));
        },
        opts
      );
    }

    case QueryType.SIMILAR: {
      return useQuery(
        [type.toString()],
        () => {
          return axios.get(urlstring('/api/similar', variables));
        },
        opts
      );
    }

    default:
      throw Error('Invalid query type');
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
  dataType: Unwrap<ReturnType<typeof ServerService['prototype']['items']>>;
  variables: Omit<
    Parameters<typeof ServerService['prototype']['items']>[0],
    'fields'
  > & {
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

type QueryActions<T = undefined> =
  | FetchProfile<T>
  | FetchItem<T>
  | FetchItems<T>
  | FetchPages<T>
  | FetchRelatedItems<T>
  | FetchSortIndexes<T>
  | FetchSimilar<T>
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
    switch (action) {
      case QueryType.ITEM: {
        return axios.get<R>(urlstring('/api/item', variables as any));
      }
      case QueryType.PROFILE: {
        return axios.get<R>(urlstring('/api/profile', variables as any));
      }
      case QueryType.PAGES: {
        return axios.get<R>(urlstring('/api/pages', variables as any));
      }

      default:
        throw Error('Invalid action type');
    }
  }
}
