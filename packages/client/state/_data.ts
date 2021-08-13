import { DataMode, ItemType } from '../misc/enums';
import { ServerItem } from '../misc/types';
import StateBlock, { defineAtom } from './_base';

export default class _DataState extends StateBlock {
  static data = defineAtom(
    { default: undefined as PartialExcept<ServerItem, 'id'> | undefined },
    true
  );

  static mode = defineAtom({ default: DataMode.DEFAULT }, true);

  static getKey(type: ItemType, data: { id: number }) {
    return `${type}-${data?.id}`;
  }
}
