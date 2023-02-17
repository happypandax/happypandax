import { DataMode, ItemType } from '../shared/enums';
import { ServerItem } from '../shared/types';
import StateBlock, { defineAtom } from './_base';

export default class _DataState extends StateBlock {
  static data = defineAtom(
    { default: undefined as PartialExcept<ServerItem, 'id'> | undefined },
    true
  );

  static persistent = defineAtom({ default: true }, true);

  static mode = defineAtom({ default: DataMode.DEFAULT }, true);

  static getKey(type: ItemType, data: { id: number }) {
    return `${type}-${data?.id}`;
  }
}
