import axios, { AxiosError, AxiosResponse } from 'axios';
import {
  useMutation,
  UseMutationOptions,
  UseMutationResult,
  useQuery,
  UseQueryOptions,
  UseQueryResult,
} from 'react-query';
import urlcat from 'urlcat';

export enum QueryType {
  GALLERIES,
  GALLERY,
}

export enum MutatationType {
  LOGIN,
  UPDATE_GALLERY,
}

axios.post<{ test2: '' }>('/api/login', { test: '' });

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
      useMutation(
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
  options?: UseQueryOptions<D, E>
): UseQueryResult<D, E> {
  switch (type) {
    case QueryType.GALLERY: {
      return useQuery(
        [type.toString(), variables],
        () => {
          return axios.get(urlcat('/api/gallery', variables));
        },
        options
      );
    }

    case QueryType.GALLERIES: {
      return useQuery(
        [type.toString(), variables],
        () => {
          return axios.get(urlcat('/api/galleries', variables));
        },
        options
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

interface FetchGalleryAction extends QueryAction {
  type: QueryType.GALLERY;
  variables: { id: number };
}

interface FetchGalleriesAction extends QueryAction {
  type: QueryType.GALLERIES;
  variables?: { limit?: number };
}

type QueryActions = FetchGalleryAction | FetchGalleriesAction;

// ======================== MUTATION ACTIONS ====================================

interface MutationAction extends Action {
  type: MutatationType;
}

interface LoginAction extends MutationAction {
  type: MutatationType.LOGIN;
  variables: { username: string; password?: string };
}

interface UpdateGalleryAction extends MutationAction {
  type: MutatationType.UPDATE_GALLERY;
  variables: { test: string };
}

type MutationActions = LoginAction | UpdateGalleryAction;
