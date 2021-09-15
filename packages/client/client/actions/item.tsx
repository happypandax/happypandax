import { ItemType, QueueType } from '../../misc/enums';
import { MutatationType, Query } from '../queries';

export class ItemActions {
  static updateMetatags(metatags, type: ItemType, item_ids: number[]) {}
  static updateFilters(filters, type: ItemType, item_ids: number[]) {}
  static queryMetadata(item_ids: number[]) {
    return Query.post(MutatationType.ADD_ITEM_TO_QUEUE, {
      item_type: ItemType.Gallery,
      item_id: item_ids,
      queue_type: QueueType.Metadata,
    });
  }
}
