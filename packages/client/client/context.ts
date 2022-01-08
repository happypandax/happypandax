import React, { useContext } from 'react';

import { ItemType } from '../misc/enums';
import { ItemSize, ServerGallery, ServerItem } from '../misc/types';

export const LibraryContext = React.createContext(undefined);

export function useLibraryContext() {
  return useContext(LibraryContext);
}

export enum ArrayContextFlag {
  None = 0,
  // item can be reomved when sent to library
  InboxRemovable = 1 << 0,
}

export interface ArrayContextT<T = any> {
  flags: ArrayContextFlag;
  data: T[];
  setData: (data: T[]) => any;
}
export const ArrayContext = React.createContext<null | ArrayContextT>(null);

export function useArrayDataContext<T>(): null | ArrayContextT<T> {
  return useContext(ArrayContext);
}

export const defaultDataContext = {
  key: '',
  type: undefined as ItemType,
  editing: false,
};
export type DataContextT = PartialExcept<
  typeof defaultDataContext,
  'key' | 'type'
>;

export const DataContext = React.createContext<DataContextT>(
  defaultDataContext
);

export function useDataContext(): DataContextT {
  return useContext(DataContext);
}

export const SearchContext = React.createContext({
  query: '',
  stateKey: '',
  ref: undefined as React.RefObject<HTMLElement>,
});

export const ReaderContext = React.createContext({
  item: undefined as DeepPick<
    ServerGallery,
    | 'id'
    | 'rating'
    | 'metatags.favorite'
    | 'metatags.inbox'
    | 'preferred_title.name'
    | 'artists.id'
    | 'grouping_id'
  >,
  stateKey: undefined as string,
});

export const ItemContext = React.createContext({
  isDragging: false,
  activity: false,
  activityContent: undefined as React.ReactNode,
  hiddenAction: undefined as boolean,
  openMenu: false,
  onMenuClose: undefined as () => void,
  size: 'medium' as ItemSize,
  ActionContent: undefined as React.ElementType,
  Details: undefined as React.ElementType,
  detailsData: undefined as PartialExcept<ServerItem, 'id'>,
  labels: [] as React.ReactNode[],
  href: '',
  disableModal: false,
  onDetailsOpen: undefined as () => void,
  hover: false,
  loading: false,
  horizontal: false,
});
