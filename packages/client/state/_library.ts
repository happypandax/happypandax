import { ItemType, ViewType } from '../misc/enums';
import StateBlock, { defineAtom } from './_base';

export default class LibraryState extends StateBlock {
  static data = defineAtom({
    default: [],
  });

  static favorites = defineAtom({
    default: false,
  });

  static filter = defineAtom({
    default: null as null | string,
  });

  static sort = defineAtom({
    default: null as null | string,
  });

  static display = defineAtom({
    default: 'card' as 'list' | 'card',
  });

  static view = defineAtom({
    default: ViewType.Library,
  });

  static item = defineAtom({
    default: ItemType.Gallery,
  });
}
