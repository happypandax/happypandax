import { ItemType } from '../misc/enums';

export class ItemActions {
  static updateMetatags(metatags, type: ItemType, item_ids: number[]) {}
  static updateFilters(filters, type: ItemType, item_ids: number[]) {}
  static queryMetadata(item_ids: number[]) {}
}
