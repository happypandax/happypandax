import StateBlock, { defineAtom } from './_base';
import { localStorageEffect } from './_statehelpers';

export default class _MiscState extends StateBlock {
  static labelAccordionOpen = defineAtom({ default: true }, true);

  static recentSearch = defineAtom(
    {
      default: [] as string[],
      effects_UNSTABLE: [localStorageEffect('recent_search')],
    },
    true
  );
}
