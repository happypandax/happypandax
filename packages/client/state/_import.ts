import { ViewID } from '../shared/types';
import StateBlock, { defineAtom } from './_base';
import { localStorageEffect } from './_statehelpers';

export default class _ImportState extends StateBlock {
  static descendingView = defineAtom(
    {
      default: false,
      effects: [localStorageEffect(undefined, { session: true })],
    },
    true
  );
  static activeImportView = defineAtom(
    {
      default: undefined as ViewID | undefined,
      effects: [localStorageEffect()],
    },
    true
  );
}
