import React, { useContext } from 'react';

import { ItemType } from '../shared/enums';
import { ItemSize, ServerGallery, ServerItem } from '../shared/types';

export const SidebarDetailsContext = React.createContext(false as boolean);
export const LibraryContext = React.createContext(false as boolean);

export function useSidebarDetailsContext() {
  return useContext(SidebarDetailsContext);
}

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

export const DataContext =
  React.createContext<DataContextT>(defaultDataContext);

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
  alternative: false,
  showMiniActionContent: undefined as boolean,
  size: 'medium' as ItemSize,
  AlternativeContent: undefined as React.ElementType,
  ActionContent: undefined as React.ElementType,
  Details: undefined as React.ElementType<{
    data: PartialExcept<ServerItem, 'id'>;
  }>,
  detailsData: undefined as PartialExcept<ServerItem, 'id'>,
  labels: undefined as React.ReactNode,
  href: '',
  disableModal: false,
  onDetailsOpen: undefined as () => void,
  hover: false,
  loading: false,
  horizontal: false,
});

export const NewItemContext = React.createContext({
  data: ServerItem,
});
