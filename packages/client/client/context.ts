import React from 'react';

import { ItemType } from '../misc/enums';
import { ServerGallery } from '../misc/types';

export const LibraryContext = React.createContext(undefined);

export const DataContext = React.createContext({
  key: '',
  type: ItemType.Gallery,
});

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
