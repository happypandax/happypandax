import { AxiosError } from 'axios';
import { useEffect, useRef, useState } from 'react';

import { CommandState } from '../shared/enums';
import { ServerErrorCode } from '../shared/error';
import { MutatationType, QueryType } from '../shared/query';
import { CommandID, CommandIDKey } from '../shared/types';
import { Query } from './queries';

import type { ErrorResponseData, RequestOptions } from '../server/requests';
import type { Server } from '../services/server';
type CommandValueMap<R = unknown> = Record<CommandIDKey, R>;

type ValueCallback<R = unknown, Scalar = false> = (
  values: Scalar extends true ? R : CommandValueMap<R>
) => void;
type ErrorCallback<Scalar = false> = (
  error: Scalar extends true
    ? ErrorResponseData
    : Record<CommandIDKey, ErrorResponseData>
) => void;

export type CommandIDs<T> = CommandID<T> | CommandID<T>[] | string[];

declare type UnwrapCommandType<T> = T extends CommandIDs<infer U> ? U : T;

interface CommandOptions<T, Scalar = false> {
  track?: boolean;
  interval?: number;
  requestOptions?: RequestOptions;
  onValue?: ValueCallback<T, Scalar>;
  onError?: ErrorCallback<Scalar>;
}

type IsScalar<T> = T extends CommandID<any> ? true : false;

export class Command<
  C extends CommandIDs<any>,
  T extends UnwrapCommandType<C> = UnwrapCommandType<C>
> {
  interval: number;
  command_ids: string[];
  scalar: boolean;
  #callbacks: {
    any: ValueCallback<T, IsScalar<C>>[];
    all: ValueCallback<T, IsScalar<C>>[];
  };
  #errorCallbacks: ErrorCallback<IsScalar<C>>[];

  #requestOptions: RequestOptions | undefined;
  #resolved_ids: { [key: CommandIDKey]: any };
  #state: { [key: CommandIDKey]: CommandState };
  #poll_id: NodeJS.Timeout | undefined;

  constructor(command_ids?: C, options?: CommandOptions<T, IsScalar<C>>) {
    this.#state = {};
    this.#resolved_ids = {};

    if (typeof command_ids === 'string') {
      this.command_ids = command_ids ? [command_ids] : [];
      this.scalar = true;
    } else {
      this.scalar = false;
      this.command_ids = command_ids ? (command_ids as string[]) : [];
    }

    this.command_ids.forEach((v) => (this.#state[v] = undefined));

    this.#callbacks = {
      any: [],
      all: [],
    };

    this.#errorCallbacks = [];

    this.interval = options?.interval ?? 1500;

    this.#requestOptions = options?.requestOptions;

    if (options?.onValue) {
      this.addCallback(options.onValue);
    }

    if (options?.onError) {
      this.addErrorCallback(options.onError);
    }

    if (options?.track ?? true) {
      this._start_poll();
    }
  }

  add(id: string, options?: { poll?: boolean }) {
    this.command_ids.push(id);
    this.#state[id] = undefined;
    if (options?.poll ?? true) {
      this._start_poll();
    }
  }

  addCallback(
    callback: ValueCallback<T, IsScalar<C>>,
    options?: { onAnyValue?: boolean; clearExisting?: boolean }
  ) {
    if (options?.clearExisting) {
      this.clearCallbacks();
    }

    if (!options?.onAnyValue) {
      this.#callbacks.any.push(callback);
    } else {
      this.#callbacks.all.push(callback);
    }
  }

  clearCallbacks() {
    this.#callbacks.any = [];
    this.#callbacks.all = [];
  }

  addErrorCallback(
    callback: ErrorCallback<IsScalar<C>>,
    options?: { clearExisting?: boolean }
  ) {
    if (options?.clearExisting) {
      this.#errorCallbacks = [];
    }

    this.#errorCallbacks.push(callback);
  }

  clearErrorCallbacks() {
    this.#errorCallbacks = [];
  }

  stopTracking() {
    this._end_poll();
  }

  _start_poll(restart = false) {
    if (this.#poll_id) {
      if (restart) {
        this._end_poll();
      } else {
        return;
      }
    }
    this.#poll_id = setTimeout(this._poll.bind(this), this.interval);
  }

  _end_poll() {
    if (this.#poll_id) {
      clearTimeout(this.#poll_id);
    }
  }

  _poll() {
    const c = this._commands_not_finished();
    if (c.length) {
      this.state()
        .then(() => {
          console.debug("Commands not finished", this._commands_not_finished())
          if (!this._commands_not_finished().length) {
            this._end_poll();
          } else {
            this.#poll_id = setTimeout(this._poll.bind(this), this.interval);
          }
        })
        .catch((e) => {
          if (
            e?.response?.status === 500 &&
            e?.response?.data?.code === ServerErrorCode.CommandError
          ) {
            // command doesn't exist, so we can ignore it
            return e.response;
          }
          throw e;
        });
    } else {
      this._end_poll();
    }
  }

  _commands_not_finished() {
    return this.command_ids
      .map((i) => {
        if (
          ![
            CommandState.Finished,
            CommandState.Failed,
            CommandState.Stopped,
          ].includes(this.#state[i])
        ) {
          return i;
        }
      })
      .filter(Boolean);
  }

  _commands_finished_successfully(unresolved = true) {
    return this.command_ids
      .map((i) => {
        if ([CommandState.Finished].includes(this.#state[i])) {
          if (unresolved) {
            if (!Object.keys(this.#resolved_ids).includes(i)) {
              return i;
            }
          } else {
            return i;
          }
        }
      })
      .filter(Boolean);
  }

  _commands_failed(unresolved = true) {
    return this.command_ids
      .map((i) => {
        if ([CommandState.Failed].includes(this.#state[i])) {
          if (unresolved) {
            if (!Object.keys(this.#resolved_ids).includes(i)) {
              return i;
            }
          } else {
            return i;
          }
        }
      })
      .filter(Boolean);
  }

  _on_state(state: Unwrap<ReturnType<Server['command_state']>>) {
    console.debug({ state })
    Object.entries(state).forEach(([k, v]) => (this.#state[k] = v));

    const c = this._commands_finished_successfully();
    if (c.length) {
      this.value(c, { raise_error: false }).then((r) => {
        Object.entries(r).forEach(([k, v]) => {
          this.#resolved_ids[k] = v;

          this.#callbacks.any.forEach((c) => c(this.scalar ? v : r));

          if (
            Object.keys(this.#resolved_ids).length === this.command_ids.length
          ) {
            this.#callbacks.all.forEach((c) =>
              c(this.scalar ? v : this.#resolved_ids)
            );
          }
        });
      });
    }

    const e = this._commands_failed();
    if (e.length) {
      this.error(e).then((r) => {
        Object.entries(r).forEach(([k, v]) => {
          this.#resolved_ids[k] = v;

          console.debug({ e, v, r, scalar: this.scalar });

          this.#errorCallbacks.forEach((c) => c(this.scalar ? v : r));
        });
      });
    }
  }

  _return<D extends Record<CommandIDKey, any>>(
    data: D,
    command_ids: string[] | string = undefined
  ): IsScalar<C> extends true ? D[CommandIDKey] : D {
    if (command_ids) {
      return typeof command_ids == 'string' ? data[command_ids] : data;
    } else {
      return this.scalar ? data[this.command_ids[0]] : data;
    }
  }

  _command_ids_param(command_ids: string[] | string = undefined) {
    if (command_ids) {
      const r = typeof command_ids === 'string' ? [command_ids] : command_ids;
      r.forEach((i) => {
        if (!this.command_ids.includes(i))
          throw Error('command ids not part of this Command instance');
      });
      return r;
    }
  }

  async state(command_ids: string[] = undefined) {
    const r = await Query.fetch(QueryType.COMMAND_STATE, {
      command_ids: this._command_ids_param(command_ids) ?? this.command_ids,
    });

    console.debug("response", r)

    this._on_state(r.data);

    return this._return(r.data, command_ids);
  }

  async start(command_ids: string[] = undefined) {
    const r = await Query.mutate(MutatationType.START_COMMAND, {
      command_ids: this._command_ids_param(command_ids) ?? this.command_ids,
    });

    return this._return(r.data, command_ids);
  }

  async stop(command_ids: string[] = undefined) {
    const r = await Query.mutate(MutatationType.STOP_COMMAND, {
      command_ids:
        this._command_ids_param(command_ids) ?? this._commands_not_finished(),
    });

    return this._return(r.data, command_ids);
  }

  async value(
    command_ids: string[] = undefined,
    args?: { raise_error?: boolean }
  ) {
    const r = await Query.fetch(QueryType.COMMAND_VALUE, {
      command_ids: this._command_ids_param(command_ids) ?? this.command_ids,
      ...args,
      __options: { ...this.#requestOptions },
    });

    return this._return(r.data, command_ids);
  }

  async error(command_ids: string[] = undefined) {
    let data: Record<CommandIDKey, ErrorResponseData | null> = {};

    for (const i of command_ids) {
      try {
        await this.value(command_ids, { raise_error: true });
        data[i] = null;
      } catch (e) {
        const err: AxiosError<ErrorResponseData> = e;
        data[i] = err.response.data;
      }
    }

    return this._return(data, command_ids);
  }
}

export function useCommand<
  C extends CommandIDs<any>,
  T extends UnwrapCommandType<C> = UnwrapCommandType<C>
>(
  command_ids: C,
  options?: Omit<CommandOptions<T, IsScalar<C>>, 'callback'> & {
    stopOnUnmount?: boolean;
    stopOnUpdate?: boolean;
  },
  callback?: CommandOptions<T, IsScalar<C>>['onValue'],
  deps: React.DependencyList = []
) {
  const optionsRef = useRef<{
    stopOnUnmount?: boolean;
    stopOnUpdate?: boolean;
  }>(options);
  const cmdRef = useRef<Command<T> | undefined>();
  const [cmd, setCmd] = useState<Command<T>>();

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const ignoreError = (e) => {
    if (
      e.response.status === 500 &&
      e.response?.data?.code === ServerErrorCode.CommandError
    ) {
      // command doesn't exist, so we can ignore it
      return e.response;
    }
    throw e;
  };

  useEffect(() => {
    return () => {
      if (cmdRef.current) {
        if (optionsRef.current?.stopOnUnmount !== false) {
          cmdRef.current.stop().catch(ignoreError);
        }
        cmdRef.current.stopTracking();
      }
    };
  }, []);

  useEffect(
    () => {
      if (cmd) {
        if (optionsRef.current?.stopOnUpdate) {
          cmd.stop().catch(ignoreError);
        }
        cmd.stopTracking();
      }

      let c;
      if (
        (Array.isArray(command_ids) && command_ids.length) ||
        (!Array.isArray(command_ids) && command_ids)
      ) {
        c = new Command(command_ids, options);
      } else {
        c = undefined;
      }

      cmdRef.current = c;
      setCmd(c);
    },
    !Array.isArray(command_ids) ? [command_ids] : [...(command_ids as string[])]
  );

  useEffect(() => {
    if (cmd && callback) {
      cmd.addCallback(callback);
    }
    return () => {
      if (cmd) {
        cmd.clearCallbacks();
      }
    };
  }, [cmd, ...deps]);

  useEffect(() => {
    if (cmd && options?.onError) {
      cmd.addErrorCallback(options.onError);
    }
    return () => {
      if (cmd) {
        cmd.clearErrorCallbacks();
      }
    };
  }, [cmd, options?.onError, ...deps]);

  return cmd;
}
