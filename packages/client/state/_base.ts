import {
  atom,
  atomFamily,
  AtomFamilyOptions,
  AtomOptions,
  ReadOnlySelectorFamilyOptions,
  ReadOnlySelectorOptions,
  ReadWriteSelectorFamilyOptions,
  ReadWriteSelectorOptions,
  RecoilState,
  RecoilValueReadOnly,
  selector,
  selectorFamily,
  SerializableParam,
} from 'recoil';

export function defineAtom<T>(
  options: MakeOptional<AtomOptions<T>, 'key'>,
  family?: false
): RecoilState<T>;

export function defineAtom<T, P extends SerializableParam = SerializableParam>(
  options: MakeOptional<AtomFamilyOptions<T, P>, 'key'>,
  family: true
): (param: P) => RecoilState<T>;
export function defineAtom<
  T,
  P extends SerializableParam = SerializableParam,
  F extends undefined | true = undefined
>(
  options:
    | MakeOptional<AtomOptions<T>, 'key'>
    | MakeOptional<AtomFamilyOptions<T, P>, 'key'>,
  family?: F
): F extends undefined ? RecoilState<T> : (param: P) => RecoilState<T> {
  return { ...options, family, _type: 'atom' } as any;
}

export function defineSelector<T>(
  options: MakeOptional<ReadOnlySelectorOptions<T>, 'key'>,
  family?: false
): RecoilValueReadOnly<T>;
export function defineSelector<T>(
  options: MakeOptional<ReadWriteSelectorOptions<T>, 'key'>,
  family?: false
): RecoilState<T>;
export function defineSelector<
  T,
  P extends SerializableParam = SerializableParam
>(
  options: MakeOptional<ReadOnlySelectorFamilyOptions<T, P>, 'key'>,
  family: true
): (param: P) => RecoilValueReadOnly<T>;
export function defineSelector<
  T,
  P extends SerializableParam = SerializableParam
>(
  options: MakeOptional<ReadWriteSelectorOptions<T>, 'key'>,
  family: true
): (param: P) => RecoilState<T>;
export function defineSelector<
  T,
  O extends
    | MakeOptional<ReadOnlySelectorOptions<T>, 'key'>
    | MakeOptional<ReadOnlySelectorFamilyOptions<T, P>, 'key'>
    | MakeOptional<ReadWriteSelectorOptions<T>, 'key'>
    | MakeOptional<ReadWriteSelectorFamilyOptions<T, P>, 'key'>,
  P extends SerializableParam = SerializableParam,
  F extends undefined | true = undefined
>(
  options: O,
  family?: F
): F extends undefined
  ? O extends MakeOptional<ReadWriteSelectorOptions<T>, 'key'>
    ? RecoilState<T>
    : RecoilValueReadOnly<T>
  : O extends MakeOptional<ReadWriteSelectorFamilyOptions<T, P>, 'key'>
  ? (param: P) => RecoilState<T>
  : (param: P) => RecoilValueReadOnly<T> {
  return { ...options, family, _type: 'selector' } as any;
}

export default class StateBlock {
  static setup(cls: StateBlock) {
    Object.keys(cls).forEach((k) => {
      const opts = { ...cls[k], family: undefined, _type: undefined };
      const key = opts.key ?? `${cls.name}_` + k;

      const func = cls[k]._type === 'atom' ? atom : selector;
      const funcFamily = cls[k]._type === 'atom' ? atomFamily : selectorFamily;

      if (cls[k].family) {
        cls[k] = funcFamily({ ...opts, key });
        cls[k].key = key;
      } else {
        cls[k] = func({ ...opts, key });
      }
    });
  }
}
