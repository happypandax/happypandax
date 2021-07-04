declare type Logger = import('./misc/logger').Logger;
declare type ServiceLocator = import('./services/base').ServiceLocator;

declare type MakeOptional<T, K extends keyof T> = Omit<T, K> &
  { [SubKey in K]?: Maybe<T[SubKey]> };

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
