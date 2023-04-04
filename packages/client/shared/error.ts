import { getEnumMembersMKeyMap } from './utility';

// IMPORTANT: Don't reorder this
export enum ErrorCode {
  UnknownError,
  NoOpError,
  ClientError,
  ServerError,
  CancelledError,
}

const ErrorCodeMembersMap = getEnumMembersMKeyMap(ErrorCode);

export class UnknownError extends Error {
  code: ErrorCode;

  __proto__?: Error;

  constructor(...args: any[]) {
    const actualProto = new.target.prototype;
    const message = args.map((v) => v.toString()).join(' ');
    super(message);
    this.message = message;
    this.code = ErrorCode[ErrorCodeMembersMap[this.name]];

    if (Object.setPrototypeOf) {
      Object.setPrototypeOf(this, actualProto);
    } else {
      // eslint-disable-next-line no-proto
      this.__proto__ = actualProto;
    }
  }

  get name() {
    return this.constructor.name;
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      code: this.code,
      stacktrace: this.stack?.split('    '),
    };
  }
}

export class NoOpError extends UnknownError {}
export class ClientError extends UnknownError {}
export class ServerError extends NoOpError {}
export class CancelledError extends NoOpError {}

// HPX SERVER ERRORS ---------------------------------------------------------------

export enum ServerErrorCode {
  CommandError = 120,
  DatabaseItemNotFoundError = 303,
}
