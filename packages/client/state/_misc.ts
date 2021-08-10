import StateBlock, { defineAtom } from './_base';

export default class _MiscState extends StateBlock {
  static label_accordion_open = defineAtom({ default: true }, true);
}
