import StateBlock, { defineAtom } from './_base';

export default class _MiscState extends StateBlock {
  static labelAccordionOpen = defineAtom({ default: true }, true);
}
