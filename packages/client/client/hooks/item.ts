import _ from 'lodash';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { SetterOrUpdater, useRecoilState } from 'recoil';

import { ItemType } from '../../shared/enums';
import { ServerItem, ServerItemWithProfile } from '../../shared/types';
import { AppState, DataState } from '../../state';
import { DataContextT, useDataContext } from '../context';
import { update } from '../utility';
import { useSetting } from './settings';

import type { GalleryCardData } from '../../components/item/Gallery';
import type { GroupingCardData } from '../../components/item/Grouping';
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

export function useAddToQueue<T extends ItemType>({ itemType, data }: {
  itemType: ItemType;
  data: T extends ItemType.Gallery ? DeepPick<GalleryCardData, 'id'> : DeepPick<GroupingCardData, 'id' | 'galleries'>
}) {
  const [readingQueue, setReadingQueue] = useRecoilState(AppState.readingQueue);

  const exists =
    itemType === ItemType.Gallery
      ? readingQueue.includes(data?.id)
      : data?.galleries?.every?.((g) => readingQueue.includes(g.id));

  const toggle = useCallback(
    (e = undefined) => {
      e?.preventDefault?.();
      e?.stopPropagation?.();

      let list = readingQueue;

      const d =
        itemType === ItemType.Gallery
          ? [data]
          : (data?.galleries as GalleryCardData[]) ?? [];


      d.forEach((g) => {
        if (exists) {
          list = list.filter((i) => i !== g.id);
        } else {
          list = [...list, g.id];
        }
      });

      setReadingQueue(list);
    },
    [data, readingQueue]
  )

  return {
    exists,
    toggle,
  }

}