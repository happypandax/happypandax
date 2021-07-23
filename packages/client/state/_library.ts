import { ItemType, ViewType } from '../misc/enums';
import StateBlock, { defineAtom } from './_base';

export class LibraryState extends StateBlock {
  static favorites = defineAtom({
    default: false,
  });

  static filter = defineAtom({
    default: undefined as number,
  });

  static sort = defineAtom({
    default: undefined as number,
  });

  static sortDesc = defineAtom({
    default: false,
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

  static itemCount = defineAtom({
    default: 30,
  });
}
