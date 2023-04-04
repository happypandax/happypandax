import {
  atom,
  atomFamily,
  AtomFamilyOptions,
  AtomOptions,
  ReadOnlySelectorFamilyOptions,
  ReadOnlySelectorOptions,
  ReadWriteSelectorFamilyOptions,
  ReadWriteSelectorOptions,
  RecoilEnv,
  RecoilState,
  RecoilValueReadOnly,
  selector,
  selectorFamily,
  SerializableParam,
} from 'recoil';

RecoilEnv.RECOIL_DUPLICATE_ATOM_KEY_CHECKING_ENABLED = false;

export function defineAtom<T>(
  options: Optional<AtomOptions<T>, 'key'>,
  family?: false
): RecoilState<T>;
export function defineAtom<T, P extends SerializableParam = SerializableParam>(
  options: Optional<AtomFamilyOptions<T, P>, 'key'>,
  family: true
): (param: P) => RecoilState<T>;
export function defineAtom<
  T,
  P extends SerializableParam = SerializableParam,
  F extends undefined | true = undefined
>(
  options:
    | Optional<AtomOptions<T>, 'key'>
    | Optional<AtomFamilyOptions<T, P>, 'key'>,
  family?: F
): F extends undefined ? RecoilState<T> : (param: P) => RecoilState<T> {
  return { ...options, family, _type: 'atom' } as any;
}

export function defineSelector<T>(
  options: Optional<ReadOnlySelectorOptions<T>, 'key'>,
  family?: false
): RecoilValueReadOnly<T>;
export function defineSelector<T>(
  options: Optional<ReadWriteSelectorOptions<T>, 'key'>,
  family?: false
): RecoilState<T>;
export function defineSelector<
  T,
  P extends SerializableParam = SerializableParam
>(
  options: Optional<ReadOnlySelectorFamilyOptions<T, P>, 'key'>,
  family: true
): (param: P) => RecoilValueReadOnly<T>;
export function defineSelector<
  T,
  P extends SerializableParam = SerializableParam
>(
  options: Optional<ReadWriteSelectorOptions<T>, 'key'>,
  family: true
): (param: P) => RecoilState<T>;
export function defineSelector<
  T,
  O extends
    | Optional<ReadOnlySelectorOptions<T>, 'key'>
    | Optional<ReadOnlySelectorFamilyOptions<T, P>, 'key'>
    | Optional<ReadWriteSelectorOptions<T>, 'key'>
    | Optional<ReadWriteSelectorFamilyOptions<T, P>, 'key'>,
  P extends SerializableParam = SerializableParam,
  F extends undefined | true = undefined
>(
  options: O,
  family?: F
): F extends undefined
  ? O extends Optional<ReadWriteSelectorOptions<T>, 'key'>
    ? RecoilState<T>
    : RecoilValueReadOnly<T>
  : O extends Optional<ReadWriteSelectorFamilyOptions<T, P>, 'key'>
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
