import _ from 'lodash';
import { useEffect } from 'react';
import { useRecoilValue } from 'recoil';

import { ActivityType, ItemType } from '../shared/enums';
import { QueryType } from '../shared/query';
import { Activity, ItemID } from '../shared/types';
import { debounceCollect } from '../shared/utility';
import { AppState } from '../state';
import { GlobalState, useGlobalValue } from '../state/global';
import { useInterval, useTabActive } from './hooks/utils';
import { Query } from './queries';
import { isElementInViewport, update } from './utility';

export type ActivityMap = { [key in ItemType]?: Record<ItemID, Activity[]> };

export class ItemActivityManager {
  private static fetch?: _.DebouncedFunc<
    (args: [ItemType, ItemID, ActivityType][]) => void
  >;
  static fetchActivity(
    type: ItemType,
    id: ItemID,
    activity_type?: ActivityType
  ) {
    if (!ItemActivityManager.fetch) {
      return;
      ItemActivityManager.fetch = debounceCollect(
        async (args) => {
          const items = {} as { [key in ItemType]?: Set<ItemID> };

          let activity: ActivityType;

          args.forEach(([type, id, activity_type]) => {
            if (!items[type]) {
              items[type] = new Set();
            }

            activity = activity_type;

            items[type].add(id);
          });

          const r = await Query.fetch(
            QueryType.ACTIVITIES,
            {
              items: _.mapValues(items, (v) => [...v]),
              activity_type: activity,
            },
            { cacheTime: 0 }
          );

          if (r.data) {
            let updated = GlobalState.activity;
            const old = updated;

            for (const [type, ids] of Object.entries(items)) {
              for (const id of ids) {
                const activities = r.data[type]?.[id];

                if (activities) {
                  updated = update(updated, {
                    [type]: (ids) =>
                      update(ids || {}, {
                        [id]: {
                          $set: activities,
                        },
                      }),
                  });
                } else {
                  if (updated?.[type]?.[id]) {
                    updated = update(updated, {
                      [type]: {
                        $unset: [id],
                      },
                    });
                  }
                }
              }
            }

            if (!_.isEqual(old, updated)) {
              GlobalState.setState({ activity: updated });
            }
          }
        },
        500,
        {
          maxWait: 3000,
          maxSize: 10000,
        }
      ); // arbitrary limit
    }

    this.fetch([[type, id, activity_type]]);
  }

  static flush() {
    if (ItemActivityManager.fetch) {
      ItemActivityManager.fetch.flush();
    }
  }

  static delayedFlush = _.throttle(
    () => {
      ItemActivityManager.flush();
    },
    1000,
    { leading: false, trailing: true }
  );
}

export function useItemActivity(
  {
    type,
    id,
    activity_type,
  }: { type?: ItemType; id?: ItemID; activity_type?: ActivityType },
  opts?: { ref?: React.RefObject<HTMLElement>; interval?: number }
) {
  const activities = useRecoilValue(
    AppState.itemActivity({ type, item_id: id })
  );

  const debug = useGlobalValue('debug');

  const tabActive = useTabActive();

  const delay =
    tabActive && type && id ? (debug ? 15000 : opts?.interval ?? 3000) : null;

  const ref = opts?.ref;

  useInterval(
    () => {
      if (ref && ref.current) {
        if (!isElementInViewport(ref.current, { offset: 500 })) return;
      }

      if (type && id) {
        ItemActivityManager.fetchActivity(type, id, activity_type);
      }
    },
    delay,
    [type, id, activity_type]
  );

  useEffect(() => {
    if (type && id) {
      ItemActivityManager.fetchActivity(type, id, activity_type);
      ItemActivityManager.delayedFlush();
    }
  }, []);

  return activities;
}
