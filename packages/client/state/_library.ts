import { ItemSort, ItemType, ViewType } from '../misc/enums';
import { ServerItem } from '../misc/types';
import StateBlock, { defineAtom } from './_base';

export default class _LibraryState extends StateBlock {
  static favorites = defineAtom({
    default: false,
  });

  static filter = defineAtom({
    default: undefined as number,
  });

  static sort = defineAtom({
    default: ItemSort.GalleryDate,
  });

  static sortDesc = defineAtom({
    default: true,
  });

  static display = defineAtom({
    default: 'card' as 'list' | 'card',
  });

  static query = defineAtom({
    default: '',
  });

  static view = defineAtom({
    default: ViewType.Library,
  });

  static item = defineAtom({
    default: ItemType.Gallery,
  });

  static limit = defineAtom({
    default: 30,
  });

  static sidebarVisible = defineAtom({
    default: false,
  });

  static sidebarData = defineAtom({
    default: undefined as PartialExcept<ServerItem, 'id'>,
  });
}
