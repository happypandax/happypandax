type UnionKeyOf<T> = import('ts-typetools').UnionKeyOf<T>;
type Primitive = import('ts-typetools').Primitive;
type DefaultGrammar = import('ts-deep-pick').DefaultGrammar;
type DeepPickGrammar = import('ts-deep-pick').DeepPickGrammar;
type DeepPickPath<
  T,
  G extends DeepPickGrammar = DefaultGrammar
> = import('ts-deep-pick').DeepPickPath<T, G>;

declare type PrettifyObject<T> = T extends Record<string, any>
  ? { [k in keyof T]: PrettifyObject<T[k]> }
  : T;

declare type DeepPick<
  T,
  K extends DeepPickPath<T, G>,
  G extends DeepPickGrammar = DefaultGrammar
> = PrettifyObject<import('ts-deep-pick').DeepPick<T, K, G>>;
declare type Logger = import('./shared/logger').Logger;
declare type ServiceLocator = import('./services/base').ServiceLocator;
declare type GetServerSession = import('./server/requests').GetServerSession;

declare type MakeRequired<T, Key extends keyof T> = T & Required<Pick<T, Key>>;

declare type MakeOptional<T, K extends keyof T> = Omit<T, K> & {
  [SubKey in K]?: Maybe<T[SubKey]>;
};

// unwrap generic
declare type Unwrap<T> = T extends Array<infer U>
  ? U
  : T extends Promise<infer U>
  ? U
  : T extends React.MutableRefObject<infer U>
  ? U
  : T extends (...args: any) => Promise<infer U>
  ? U
  : T extends (...args: any) => infer U
  ? U
  : T;

declare const $Opaque = Symbol('Opaque');

declare interface Opaque {
  [$Opaque]?: never;
}

// like DeepPickPath but without tokens also with globs
declare type DeepPickPathPlain<T, Glob extends string = '.*'> = (
  | (T extends Opaque
      ? never
      : T extends Primitive
      ? never
      : T extends Array<infer T>
      ? _InnerKey<T, '', Glob>
      : {
          [key in _KeyOfUnion<T>]: key | _InnerKey<T[key], key, Glob, T>;
        }[_KeyOfUnion<T>])
  | '*'
) &
  string;

// like DeepPickPathPlain but without globs
declare type DeepPickPathPlainWithoutGlob<T, Glob extends string = ''> =
  | T extends Opaque
      ? never
      : T extends Primitive
      ? never
      : T extends Array<infer T>
      ? _InnerKey<T, '', Glob>
      : {
          [key in _KeyOfUnion<T>]: key | _InnerKey<T[key], key, Glob, T>;
        }[_KeyOfUnion<T>] &
  string;

declare type DeepPartial<T> = T extends object
  ? {
      [P in keyof T]?: DeepPartial<T[P]>;
    }
  : T;

type _InnerKey<
  T,
  key extends string,
  Glob extends string,
  parentType = undefined
> = (
  T extends Opaque
    ? never
    : T extends Primitive
    ? never
    : T extends Array<infer T>
    ? T extends Primitive
      ? never
      : `${key}${_InnerKey<T, '', Glob> & string}` | `${key}${Glob}`
    : T extends parentType
    ? `${key}`
    : {
        [key2 in _KeyOfUnion<T>]:
          | `${key}${Glob}`
          | `${key}${'.'}${key2}`
          | `${key}${'.'}${_InnerKey<T[key2], key2, Glob> & string}`;
      }[_KeyOfUnion<T>]
) extends infer key
  ? key
  : never;

type _KeyOfUnion<T> = UnionKeyOf<T> & string;

declare type GetComponentProps<T> = T extends
  | React.ComponentType<infer P>
  | React.ElementType<infer P>
  ? P
  : never;

declare type ValueOf<T> = T[keyof T];

// Flatten an intersection type by merging keys:
declare type Flatten<T> = T extends Record<string, any>
  ? { [k in keyof T]: T[k] }
  : never;

declare type DiscriminateUnion<
  T,
  K extends keyof T,
  V extends T[K]
> = T extends Record<K, V> ? T : never;

declare type RecordValueMap<T, V> = {
  [P in keyof T]: V;
};

declare type RecordFromUnion<T extends Record<K, string>, K extends keyof T> = {
  [V in T[K]]: DiscriminateUnion<T, K, V>;
};

declare type RecordFromUnionWithPick<
  T extends Record<K, string>,
  K extends keyof T,
  P extends keyof T
> = {
  [V in T[K]]: Pick<DiscriminateUnion<T, K, V>, P>;
};

declare type RecordFromUnionWithOmit<
  T extends Record<K, string>,
  K extends keyof T,
  P extends keyof T
> = {
  [V in T[K]]: Omit<DiscriminateUnion<T, K, V>, P>;
};

// A better Omit
declare type DistributiveOmit<T, K extends keyof T> = T extends unknown
  ? Omit<T, K>
  : never;

declare type PartialExcept<T, K extends keyof T> = Pick<T, K> & Partial<T>;

declare type RecursivePartial<T> = {
  [P in keyof T]?: T[P] extends (infer U)[]
    ? RecursivePartial<U>[]
    : T[P] extends object
    ? RecursivePartial<T[P]>
    : T[P];
};

declare type Optional<T, K extends keyof T> = Omit<T, K> & Partial<T>;

declare type Replace<
  T,
  P extends keyof T,
  R extends Partial<Record<keyof T, any>>
> = Omit<T, P> & R;

declare module NodeJS {
  interface Global {
    app: {
      title: string;
      initialized: boolean;
      IS_SERVER: boolean;
      log: Logger;
      service: ServiceLocator;
      getServerSession: GetServerSession;

      /// dev only
      hpx_sessions: any;
      hpx_clients: any;
      hpx_pool: any;
    };
    log: Logger;
  }
}
