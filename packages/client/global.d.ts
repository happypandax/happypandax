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
declare type Logger = import('./misc/logger').Logger;
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

declare module NodeJS {
  interface Global {
    app: {
      title: string;
      initialized: boolean;
      IS_SERVER: boolean;
      log: Logger;
      service: ServiceLocator;
    };
  }
}
