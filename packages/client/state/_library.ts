import { ItemSort, ItemType, ViewType } from '../shared/enums';
import { ServerItem } from '../shared/types';
import StateBlock, { defineAtom } from './_base';
import { cookieEffect, localStorageEffect } from './_statehelpers';

export default class _LibraryState extends StateBlock {
  static favorites = defineAtom(
    {
      default: false,
      effects: [cookieEffect()],
    },
    true
  );

  static filter = defineAtom(
    {
      default: undefined as number,
      effects: [cookieEffect()],
    },
    true
  );

  static sort = defineAtom(
    {
      default: ItemSort.GalleryDate,
      effects: [cookieEffect()],
    },
    true
  );

  static sortDesc = defineAtom(
    {
      default: true,
      effects: [cookieEffect()],
    },
    true
  );

  static display = defineAtom({
    default: 'card' as 'list' | 'card',
    effects: [cookieEffect()],
  });

  static query = defineAtom(
    {
      default: '',
      effects: [
        localStorageEffect((n) => n.key, { session: true }),
        cookieEffect((n) => n.key, {
          noInitialValue: true,
          removeIfNoInitialValue: true,
        }),
      ],
    },
    true
  );

  static view = defineAtom(
    {
      default: ViewType.Library,
      effects: [cookieEffect()],
    },
    true
  );

  static item = defineAtom(
    {
      default: ItemType.Gallery,
      effects: [cookieEffect()],
    },
    true
  );

  static limit = defineAtom({
    default: 30,
    effects: [cookieEffect()],
  });

  static page = defineAtom(
    {
      default: 1,
      effects: [
        ({ setSelf, onSet }) => {
          onSet((newValue) => {
            if (isNaN(newValue)) {
              setSelf(1);
            } else {
              setSelf(newValue);
            }
          });
        },
        cookieEffect(),
      ],
    },
    true
  );

  static series = defineAtom({
    default: true,
    effects: [cookieEffect()],
  });

  static infinite = defineAtom({
    default: false,
    effects: [localStorageEffect()],
  });

  static sidebarVisible = defineAtom({
    default: false,
  });

  static sidebarData = defineAtom({
    default: undefined as PartialExcept<ServerItem, 'id'>,
  });
}
