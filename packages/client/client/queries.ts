import axios, { AxiosError, AxiosResponse } from 'axios';
import {
  InitialDataFunction,
  useMutation,
  UseMutationOptions,
  UseMutationResult,
  useQuery,
  UseQueryOptions,
  UseQueryResult,
} from 'react-query';

import { ItemType } from '../misc/enums';
import { ServerSortIndex } from '../misc/types';
import { urlstring } from '../misc/utility';

export enum QueryType {
  ITEMS,
  ITEM,
  GALLERIES,
  GALLERY,
  SORT_INDEXES,
  SERVER_STATUS,
}

export enum MutatationType {
  LOGIN,
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

export function useQueryType<
  T extends QueryActions,
  K extends T['type'],
  V extends Extract<T, { type: K }>['variables'],
  R extends Extract<T, { type: K }>['dataType'],
  D extends AxiosResponse<R>,
  E extends AxiosError<D>
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
    case QueryType.GALLERY: {
      return useQuery(
        [type.toString(), variables],
        () => {
          return axios.get(urlstring('/api/gallery', variables));
        },
        opts
      );
    }

    case QueryType.GALLERIES: {
      return useQuery(
        [type.toString(), variables],
        () => {
          return axios.get(urlstring('/api/galleries', variables));
        },
        opts
      );
    }

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

    case QueryType.ITEMS: {
      return useQuery(
        [type.toString()],
        () => {
          return axios.get(urlstring('/api/items', variables));
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

interface QueryAction extends Action {
  type: QueryType;
}

interface FetchGallery extends QueryAction {
  type: QueryType.GALLERY;
  variables: { id: number };
}

interface FetchGalleries extends QueryAction {
  type: QueryType.GALLERIES;
  variables?: { limit?: number };
}

interface FetchServerStatus extends QueryAction {
  type: QueryType.SERVER_STATUS;
  dataType: {
    loggedIn: boolean;
    connected: boolean;
  };
}

interface FetchSortIndexes extends QueryAction {
  type: QueryType.SORT_INDEXES;
  dataType: ServerSortIndex[];
  variables: { item_type: ItemType; translate?: boolean; locale?: string };
}

interface FetchItems extends QueryAction {
  type: QueryType.ITEMS;
  dataType: Record<string, any>[];
  variables: { item_type: ItemType; limit?: number; offset?: number };
}

type QueryActions =
  | FetchItems
  | FetchSortIndexes
  | FetchServerStatus
  | FetchGallery
  | FetchGalleries;

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
