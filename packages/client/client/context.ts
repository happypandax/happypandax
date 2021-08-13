import React from 'react';

import { ItemType } from '../misc/enums';

export const LibraryContext = React.createContext(undefined);

export const DataContext = React.createContext({
  key: '',
  type: ItemType.Gallery,
});
