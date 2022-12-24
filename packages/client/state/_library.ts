import { syncEffect } from 'recoil-sync';

import { string } from '@recoiljs/refine';

import { ItemSort, ItemType, ViewType } from '../shared/enums';
import { ServerItem } from '../shared/types';
import StateBlock, { defineAtom } from './_base';
import { cookieEffect, localStorageEffect } from './_statehelpers';

export default class _LibraryState extends StateBlock {
  static favorites = defineAtom(
    {
      default: false,
      effects_UNSTABLE: [cookieEffect()],
    },
    true
  );

  static filter = defineAtom(
    {
      default: undefined as number,
      effects_UNSTABLE: [cookieEffect()],
    },
    true
  );

  static sort = defineAtom(
    {
      default: ItemSort.GalleryDate,
      effects_UNSTABLE: [cookieEffect()],
    },
    true
  );

  static sortDesc = defineAtom(
    {
      default: true,
      effects_UNSTABLE: [cookieEffect()],
    },
    true
  );

  static display = defineAtom({
    default: 'card' as 'list' | 'card',
    effects_UNSTABLE: [cookieEffect()],
  });

  static query = defineAtom(
    {
      default: '',
      effects_UNSTABLE: [
        localStorageEffect((n) => n.key, { session: true }),
        cookieEffect((n) => n.key, {
          noInitialValue: true,
          removeIfNoInitialValue: true,
        }),
        syncEffect({refine: string(), syncDefault: false, storeKey: "q"}),
      ],
    },
    true
  );

  static view = defineAtom(
    {
      default: ViewType.Library,
      effects_UNSTABLE: [cookieEffect()],
    },
    true
  );

  static item = defineAtom(
    {
      default: ItemType.Gallery,
      effects_UNSTABLE: [cookieEffect()],
    },
    true
  );

  static limit = defineAtom({
    default: 30,
    effects_UNSTABLE: [cookieEffect()],
  });

  static page = defineAtom(
    {
      default: 1,
      effects_UNSTABLE: [
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
    effects_UNSTABLE: [cookieEffect()],
  });

  static infinite = defineAtom({
    default: false,
    effects_UNSTABLE: [localStorageEffect()],
  });

  static sidebarVisible = defineAtom({
    default: false,
  });

  static sidebarData = defineAtom({
    default: undefined as PartialExcept<ServerItem, 'id'>,
  });
}
