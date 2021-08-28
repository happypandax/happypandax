import { ItemSort, ItemType, ViewType } from '../misc/enums';
import { ServerItem } from '../misc/types';
import StateBlock, { defineAtom } from './_base';
import { localStorageEffect } from './_statehelpers';

export default class _LibraryState extends StateBlock {
  static favorites = defineAtom({
    default: false,
    effects_UNSTABLE: [localStorageEffect('library_fav')],
  });

  static filter = defineAtom({
    default: undefined as number,
    effects_UNSTABLE: [localStorageEffect('library_filter')],
  });

  static sort = defineAtom({
    default: ItemSort.GalleryDate,
    effects_UNSTABLE: [localStorageEffect('library_sort')],
  });

  static sortDesc = defineAtom({
    default: true,
    effects_UNSTABLE: [localStorageEffect('library_sort_desc')],
  });

  static display = defineAtom({
    default: 'card' as 'list' | 'card',
    effects_UNSTABLE: [localStorageEffect('library_display')],
  });

  static query = defineAtom({
    default: '',
    effects_UNSTABLE: [localStorageEffect('library_query', { session: true })],
  });

  static view = defineAtom({
    default: ViewType.Library,
    effects_UNSTABLE: [localStorageEffect('library_view')],
  });

  static item = defineAtom({
    default: ItemType.Gallery,
    effects_UNSTABLE: [localStorageEffect('library_item')],
  });

  static limit = defineAtom({
    default: 30,
    effects_UNSTABLE: [localStorageEffect('library_limit')],
  });

  static infinite = defineAtom({
    default: false,
    effects_UNSTABLE: [localStorageEffect('library_infinite')],
  });

  static sidebarVisible = defineAtom({
    default: false,
  });

  static sidebarData = defineAtom({
    default: undefined as PartialExcept<ServerItem, 'id'>,
  });
}
