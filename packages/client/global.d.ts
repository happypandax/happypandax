declare type Logger = import('./misc/logger').Logger;

declare module NodeJS {
  interface Global {
    app: {
      title: string;
      initialized: boolean;
      IS_SERVER: boolean;
      log: Logger;
    };
  }
}
