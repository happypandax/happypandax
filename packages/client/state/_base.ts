import { atom, AtomOptions, RecoilState } from 'recoil';

type AtomOptionsOptional<T = unknown> = MakeOptional<AtomOptions<T>, 'key'>;

export function defineAtom<T>(options: AtomOptionsOptional<T>) {
  return (options as unknown) as RecoilState<T>;
}

export default class StateBlock {
  static setup(cls: StateBlock) {
    Object.keys(cls).forEach((k) => {
      const opts: AtomOptionsOptional = cls[k];
      cls[k] = atom({ ...opts, key: opts.key ?? `${cls.name}_` + k });
    });
  }
}
