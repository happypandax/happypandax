import { SearchOptions } from '../shared/types';
import StateBlock, { defineAtom } from './_base';
import { cookieEffect, localStorageEffect } from './_statehelpers';

export default class _SearchState extends StateBlock {
  static recent = defineAtom(
    {
      default: [] as string[],
      effects_UNSTABLE: [localStorageEffect()],
    },
    true
  );

  static dynamic = defineAtom(
    {
      default: false,
      effects_UNSTABLE: [localStorageEffect()],
    },
    true
  );

  static suggest = defineAtom(
    {
      default: true,
      effects_UNSTABLE: [localStorageEffect()],
    },
    true
  );

  static options = defineAtom(
    {
      default: {} as SearchOptions,
      effects_UNSTABLE: [cookieEffect((n) => n.key)],
    },
    true
  );
}
