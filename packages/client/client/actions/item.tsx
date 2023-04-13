import { AxiosResponse } from 'axios';

import { ItemType } from '../../shared/enums';
import { MutatationType } from '../../shared/query';
import { ServerItem, ServerItemWithMetatags } from '../../shared/types';
import { Query } from '../queries';
import { update } from '../utility';

import type { Server } from '../../services/server';
export class ItemActions {
  static async newItem<T extends Partial<ServerItem>>(
    data: T,
    args: Omit<Parameters<Server['new_item']>[0], 'item'>,
    onNewData?: (data: T, mutated: boolean) => void
  ) {
    return new Promise<AxiosResponse<boolean>>((resolve, reject) => {
      let mutated = false;
      const newData = data;

      // TODO: optimistic update

      if (mutated) {
        onNewData?.(newData, mutated);
      }

      Query.mutate(
        MutatationType.NEW_ITEM,
        { ...args, item: newData },
        {
          onSettled: (res, err, variables) => {
            // return original data if error
            if ((err || !res.data) && mutated) {
              onNewData?.(data, mutated);
            }

            // need to be last
            if (err) {
              reject(err);
            } else {
              resolve(res);
            }
          },
        },
        { method: 'POST' }
      ).catch(reject);
    });
  }

  static async updateItem<T extends Partial<ServerItem>>(
    item_id: number,
    data: T,
    args: Parameters<Server['update_item']>[0],
    onUpdatedData?: (data: T, mutated: boolean) => void
  ) {
    return new Promise<AxiosResponse<boolean>>((resolve, reject) => {
      let mutated = false;
      let updatedData = data;
      const newData = { id: item_id, ...args.item };

      // optimistic update

      Object.keys(newData).forEach((k) => {
        // simple assignment
        if (['rating'].includes(k)) {
          updatedData = update(updatedData as Record<string, any>, {
            [k]: () => newData[k],
          }) as T;
          mutated = true;
        }
      });

      if (mutated) {
        onUpdatedData?.(updatedData, mutated);
      }

      Query.mutate(
        MutatationType.UPDATE_ITEM,
        { ...args, item: newData },
        {
          onSettled: (res, err, variables) => {
            // return original data if error
            if ((err || !res.data) && mutated) {
              onUpdatedData?.(data, mutated);
            }

            // need to be last
            if (err) {
              reject(err);
            } else {
              resolve(res);
            }
          },
        },
        {
          method: 'PATCH',
        }
      ).catch(reject);
    });
  }

  static async updateMetatags<
    T extends RecursivePartial<ServerItemWithMetatags>
  >(
    data: T[],
    args: Parameters<Server['update_metatags']>[0],
    onUpdatedData?: (data: T[], mutated: boolean) => void
  ) {
    return new Promise<AxiosResponse<boolean | number>>((resolve, reject) => {
      let mutated = false;
      let updatedData = data;

      // optimistic update

      updatedData = data.map((d) => {
        // simple assignment
        let nd = d;
        Object.entries(args.metatags).forEach(([k, v]) => {
          if (nd?.metatags?.[k] !== v) {
            nd = update(nd, { metatags: { [k]: () => v } });
            mutated = true;
          }
        });

        return nd;
      });

      if (mutated) {
        onUpdatedData?.(updatedData, mutated);
      }

      Query.mutate(MutatationType.UPDATE_METATAGS, args, {
        onSettled: (res, err, variables) => {
          // return original data if error
          if ((err || !res.data) && mutated) {
            onUpdatedData?.(data, mutated);
          }

          // TODO: only resolve after handling the command id

          // need to be last
          if (err) {
            reject(err);
          } else {
            resolve(res);
          }
        },
      }).catch(reject);
    });
  }

  static updateFilters(filters, type: ItemType, item_ids: number[]) {}

  static openGallery() {}
}
