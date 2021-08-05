import { ImageSize, ItemFit, ReadingDirection } from '../misc/enums';
import StateBlock, { defineAtom } from './_base';

export default class _ReaderState extends StateBlock {
  static fit = defineAtom({ default: ItemFit.Auto }, true);

  static pageNumber = defineAtom({ default: 1 }, true);

  static pageCount = defineAtom({ default: 0 }, true);

  static endReached = defineAtom({ default: false }, true);

  static scaling = defineAtom({ default: 0 as ImageSize }, true);

  static autoNavigateInterval = defineAtom({ default: 20 }, true);

  static autoNavigateCounter = defineAtom({ default: 0 }, true);

  static autoNavigate = defineAtom({ default: false }, true);

  static stretchFit = defineAtom({ default: false }, true);

  static wheelZoom = defineAtom({ default: false }, true);

  static direction = defineAtom(
    { default: ReadingDirection.TopToBottom },
    true
  );
}
