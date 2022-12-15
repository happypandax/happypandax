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

declare type MakeOptional<T, K extends keyof T> = Omit<T, K> &
  { [SubKey in K]?: Maybe<T[SubKey]> };

// unwrap generic
declare type Unwrap<T> = T extends Array<infer U>
  ? U
  : T extends Promise<infer U>
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

declare module NodeJS {
  interface Global {
    app: {
      title: string;
      initialized: boolean;
      IS_SERVER: boolean;
      log: Logger;
      service: ServiceLocator;
    };
    log: Logger;
  }
}
