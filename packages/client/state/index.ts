import { AppState } from './_app';
import StateBlock from './_base';
import { LibraryState } from './_library';

((...cls: StateBlock[]) => {
  cls.forEach((c) => StateBlock.setup(c));
})(AppState, LibraryState);

export { AppState, LibraryState };
