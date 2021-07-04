import AppState from './_app';
import LibraryState from './_library';
import StateBlock from './base';

((...cls: StateBlock[]) => {
  cls.forEach((c) => StateBlock.setup(c));
})(AppState, LibraryState);

export { AppState, LibraryState };
