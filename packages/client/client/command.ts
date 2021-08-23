import axios from 'axios';
import { useEffect, useState } from 'react';

import { CommandState } from '../misc/enums';
import { CommandID, CommandIDKey } from '../misc/types';
import { urlstring } from '../misc/utility';
import ServerService from '../services/server';

type ValueCallback<R = unknown> = (values: Record<CommandIDKey, R>) => void;

type CommandIDs<T> = CommandID<T> | number[];

interface CommandOptions<T> {
  poll?: boolean;
  interval?: number;
  callback?: ValueCallback<T>;
}

export class Command<T = unknown> {
  interval: number;
  command_ids: number[];
  scalar: boolean;
  #callbacks: {
    any: ValueCallback[];
    all: ValueCallback[];
  };

  #resolved_ids: { [key: CommandIDKey]: any };
  #state: { [key: CommandIDKey]: CommandState };
  #poll_id: NodeJS.Timeout | undefined;

  constructor(command_ids?: CommandIDs<T>, options?: CommandOptions<T>) {
    this.#state = {};
    this.#resolved_ids = {};

    if (typeof command_ids === 'number') {
      this.command_ids = command_ids ? [command_ids] : [];
      this.scalar = true;
    } else {
      this.scalar = false;
      this.command_ids = command_ids ? (command_ids as number[]) : [];
    }

    this.command_ids.forEach((v) => (this.#state[v.toString()] = undefined));

    this.#callbacks = {
      any: [],
      all: [],
    };

    this.interval = options?.interval ?? 1500;

    if (options?.callback) {
      this.setCallback(options.callback);
    }

    if (options?.poll ?? true) {
      this._start_poll();
    }
  }

  add(id: number, options?: { poll?: boolean }) {
    this.command_ids.push(id);
    this.#state[id.toString()] = undefined;
    if (options?.poll ?? true) {
      this._start_poll();
    }
  }

  setCallback(callback: ValueCallback, options?: { onAnyValue?: boolean }) {
    if (!options?.onAnyValue) {
      this.#callbacks.any.push(callback);
    } else {
      this.#callbacks.all.push(callback);
    }
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
      this.state().then(() => {
        if (!this._commands_not_finished().length) {
          this._end_poll();
        } else {
          this.#poll_id = setTimeout(this._poll.bind(this), this.interval);
        }
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
            CommandState.finished,
            CommandState.failed,
            CommandState.stopped,
          ].includes(this.#state[i.toString()])
        ) {
          return i;
        }
      })
      .filter(Boolean);
  }

  _commands_finished_successfully(unresolved = true) {
    return this.command_ids
      .map((i) => {
        if ([CommandState.finished].includes(this.#state[i.toString()])) {
          if (unresolved) {
            if (!Object.keys(this.#resolved_ids).includes(i.toString())) {
              return i;
            }
          } else {
            return i;
          }
        }
      })
      .filter(Boolean);
  }

  _on_state(state: Unwrap<ReturnType<ServerService['command_state']>>) {
    Object.entries(state).forEach(([k, v]) => (this.#state[k] = v));

    const c = this._commands_finished_successfully();
    if (c.length) {
      this.value(c).then((r) => {
        Object.entries(r).forEach(([k, v]) => {
          this.#resolved_ids[k] = v;

          this.#callbacks.any.forEach((c) => c(r));

          if (
            Object.keys(this.#resolved_ids).length === this.command_ids.length
          ) {
            this.#callbacks.all.forEach((c) => c(this.#resolved_ids));
          }
        });
      });
    }
  }

  _return(
    data: Record<CommandIDKey, any>,
    command_ids: number[] | number = undefined
  ) {
    if (command_ids) {
      const s = typeof command_ids == 'number' ? true : undefined;
      return s ? data[command_ids.toString()] : data;
    } else {
      return this.scalar ? data[this.command_ids[0].toString()] : data;
    }
  }

  _command_ids_param(command_ids: number[] | number = undefined) {
    if (command_ids) {
      const r = typeof command_ids === 'number' ? [command_ids] : command_ids;
      r.forEach((i) => {
        if (!this.command_ids.includes(i))
          throw Error('command ids not part of this Command instance');
      });
      return r;
    }
  }

  async state(command_ids: number[] = undefined) {
    const r = await axios.patch<
      Unwrap<ReturnType<ServerService['command_state']>>
    >(
      urlstring('/api/command', {
        command_ids: this._command_ids_param(command_ids) ?? this.command_ids,
      })
    );

    this._on_state(r.data);

    return this._return(r.data, command_ids);
  }

  async start(command_ids: number[] = undefined) {
    const r = await axios.post<
      Unwrap<ReturnType<ServerService['start_command']>>
    >(
      urlstring('/api/command', {
        command_ids: this._command_ids_param(command_ids) ?? this.command_ids,
      })
    );
    return this._return(r.data, command_ids);
  }

  async stop(command_ids: number[] = undefined) {
    const r = await axios.delete<
      Unwrap<ReturnType<ServerService['stop_command']>>
    >(
      urlstring('/api/command', {
        command_ids:
          this._command_ids_param(command_ids) ?? this._commands_not_finished(),
      })
    );
    return this._return(r.data, command_ids);
  }

  async value(command_ids: number[] = undefined) {
    const r = await axios.get<
      Unwrap<ReturnType<ServerService['command_value']>>
    >(
      urlstring('/api/command', {
        command_ids: this._command_ids_param(command_ids) ?? this.command_ids,
      })
    );
    return this._return(r.data, command_ids);
  }
}

export function useCommand<T = unknown>(
  command_ids: CommandIDs<T>,
  options: CommandOptions<T>
) {
  const [cmd, setCmd] = useState<Command<T>>();

  useEffect(
    () => {
      if (command_ids) {
        setCmd(new Command(command_ids, options));
      } else {
        setCmd(undefined);
      }
    },
    typeof command_ids === 'number' ? [command_ids] : (command_ids as number[])
  );

  return cmd;
}
