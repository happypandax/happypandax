import _ from 'lodash';
import { useEffect, useMemo, useState } from 'react';
import { SetterOrUpdater, useRecoilState } from 'recoil';

import { ItemType } from '../../misc/enums';
import { ServerItem, ServerItemWithProfile } from '../../misc/types';
import { update } from '../../misc/utility';
import { DataState } from '../../state';
import { DataContextT, useDataContext } from '../context';
import { useSetting } from './settings';

const defaultImage = '/img/default.png';
const errorImage = '/img/error-image.png';
const noImage = '/img/no-image.png';

export type ImageSource = string | ServerItemWithProfile['profile'];

export function useImage(initialSrc?: ImageSource) {
  const [error, setError] = useState(false);
  const [loaded, setLoaded] = useState(initialSrc ? false : true);
  const src = useMemo(() => {
    if (error) {
      return errorImage;
    }

    const s = !initialSrc
      ? noImage
      : typeof initialSrc === 'string'
      ? initialSrc
      : initialSrc.data
      ? initialSrc.data
      : noImage;

    if (loaded) {
      return s;
    }

    const img = new Image();
    img.src = s;
    if (img.complete) {
      return s;
    }
    img.addEventListener('load', () => setLoaded(true));
    img.addEventListener('error', () => setError(true));

    return defaultImage;
  }, [initialSrc, loaded, error]);

  return { src, loaded, setLoaded, error, setError };
}

export function useSetupDataState<T extends PartialExcept<ServerItem, 'id'>>({
  initialData,
  itemType,
  key = '',
}: {
  itemType: ItemType;
  initialData?: T;
  key?: string;
}) {
  const contextKey = DataState.getKey(itemType, initialData) + key;

  const [stateData, setData] = useRecoilState(DataState.data(contextKey));

  const data = (stateData as T) ?? initialData;

  useEffect(() => {
    setData(initialData as T);
  }, [initialData]);

  const dataContext: DataContextT = {
    key: contextKey,
    type: itemType,
  };

  return {
    data,
    setData: setData as SetterOrUpdater<T>,
    dataContext,
  };
}

export function useUpdateDataState<T extends Partial<ServerItem>>(
  defaultData?: T,
  props?: {}
) {
  const ctx = useDataContext();

  const [data, setData] = useRecoilState(DataState.data(ctx.key));

  return {
    key: ctx.key,
    data: ctx.key ? (data as T) ?? defaultData : undefined,
    setData: ctx.key ? (setData as SetterOrUpdater<T>) : undefined,
    updateData: ctx.key ? _.partial(update, data) : undefined,
    context: ctx,
  };
}

export interface RecentItem {
  id: number;
  type: ItemType;
}

export function useRecentViewedItem() {
  const [recents] = useSetting<RecentItem[]>('user.recently_viewed', [], {
    cacheTime: 0,
  });

  return recents;
}

export function useUpdateRecentlyViewedItem(id: number, type: ItemType) {
  const [recents, setRecents] = useSetting<RecentItem[] | false>(
    'user.recently_viewed',
    false
  );

  useEffect(() => {
    if (id && type && recents) {
      // remove if exists
      const newRecents = [
        { id, type },
        ...recents.filter((r) => !(r.id === id && r.type === type)),
      ];

      const count = 20;

      setRecents(newRecents.slice(0, count));
    }
  }, [id, type, typeof recents === 'boolean']);
}
