

import StateBlock, { defineAtom } from './base';

export default class AppState extends StateBlock {
  static theme = defineAtom({
    default: 'light' as 'light' | 'dark',
  });
}
