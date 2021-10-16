import { ItemSort, ItemType, ViewType } from '../misc/enums';
import { ServerItem } from '../misc/types';
import StateBlock, { defineAtom } from './_base';
import { cookieEffect, localStorageEffect } from './_statehelpers';

export default class _LibraryState extends StateBlock {
  static favorites = defineAtom({
    default: false,
    effects_UNSTABLE: [
      localStorageEffect('library_fav'),
      cookieEffect('library_fav'),
    ],
  });

  static filter = defineAtom({
    default: undefined as number,
    effects_UNSTABLE: [
      localStorageEffect('library_filter'),
      cookieEffect('library_filter'),
    ],
  });

  static sort = defineAtom({
    default: ItemSort.GalleryDate,
    effects_UNSTABLE: [
      localStorageEffect('library_sort'),
      cookieEffect('library_sort'),
    ],
  });

  static sortDesc = defineAtom({
    default: true,
    effects_UNSTABLE: [
      localStorageEffect('library_sort_desc'),
      cookieEffect('library_sort_desc'),
    ],
  });

  static display = defineAtom({
    default: 'card' as 'list' | 'card',
    effects_UNSTABLE: [
      localStorageEffect('library_display'),
      cookieEffect('library_display'),
    ],
  });

  static query = defineAtom({
    default: '',
    effects_UNSTABLE: [
      localStorageEffect('library_query', { session: true }),
      cookieEffect('library_query', {
        noInitialValue: true,
        removeIfNoInitialValue: true,
      }),
    ],
  });

  static view = defineAtom({
    default: ViewType.Library,
    effects_UNSTABLE: [
      localStorageEffect('library_view'),
      cookieEffect('library_view'),
    ],
  });

  static item = defineAtom({
    default: ItemType.Gallery,
    effects_UNSTABLE: [
      localStorageEffect('library_item'),
      cookieEffect('library_item'),
    ],
  });

  static limit = defineAtom({
    default: 30,
    effects_UNSTABLE: [
      localStorageEffect('library_limit'),
      cookieEffect('library_limit'),
    ],
  });

  static series = defineAtom({
    default: true,
    effects_UNSTABLE: [
      localStorageEffect('library_series'),
      cookieEffect('library_series'),
    ],
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
