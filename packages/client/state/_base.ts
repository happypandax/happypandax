import {
  atom,
  atomFamily,
  AtomFamilyOptions,
  AtomOptions,
  RecoilState,
  SerializableParam,
} from 'recoil';

type AtomOptionsOptional<T = unknown> = MakeOptional<AtomOptions<T>, 'key'>;
type AtomFamilyOptionsOptional<
  T = unknown,
  P extends SerializableParam = SerializableParam
> = MakeOptional<AtomFamilyOptions<T, P>, 'key'>;

export function defineAtom<
  T,
  P extends SerializableParam = SerializableParam,
  F extends undefined | true = undefined
>(
  options: AtomOptionsOptional<T> | AtomFamilyOptionsOptional<T, P>,
  family?: F
): F extends undefined ? RecoilState<T> : (param: P) => RecoilState<T> {
  return { ...options, family } as any;
}

export default class StateBlock {
  static setup(cls: StateBlock) {
    Object.keys(cls).forEach((k) => {
      const opts = { ...cls[k], family: undefined };
      if (cls[k].family) {
        cls[k] = atomFamily({ ...opts, key: opts.key ?? `${cls.name}_` + k });
      } else {
        cls[k] = atom({ ...opts, key: opts.key ?? `${cls.name}_` + k });
      }
    });
  }
}
