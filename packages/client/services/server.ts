import Client, {
  AnyJson,
  JsonArray,
  JsonMap,
  log,
  ServerErrorMsg,
  ServerMsg,
} from 'happypandax-client';

import { createCache } from '../misc/cache';
import {
  CommandState,
  ItemsKind,
  ItemType,
  LogType,
  PluginState,
  Priority,
  QueueType,
} from '../misc/enums';
import {
  CommandID,
  CommandIDKey,
  CommandProgress,
  DownloadHandler,
  DownloadItem,
  FieldPath,
  MetadataHandler,
  MetadataItem,
  PluginData,
  ProfileOptions,
  SearchItem,
  SearchOptions,
  ServerGallery,
  ServerItem,
  ServerMetaTags,
  ServerPage,
  ServerSortIndex,
  SortOptions,
  Version,
} from '../misc/types';
import { Service } from './base';
import { ServiceType } from './constants';

export default class ServerService extends Service {
  cache: ReturnType<typeof createCache>;
  endpoint: { host: string; port: number };

  #client: Client;

  constructor(endpoint?: { host: string; port: number }) {
    super(ServiceType.Server);

    log.enabled = false;
    log.logger = {
      debug: global.app.log.d,
      info: global.app.log.i,
      warning: global.app.log.w,
      error: global.app.log.e,
    };

    // this avoiding recreating the hpx client during HMR
    this.#client =
      global.app?.hpx_client ?? new Client({ name: 'next-client' });
    global.app.hpx_client = this.#client;
    this.cache = global.app?.hpx_cache ?? createCache();
    global.app.hpx_cache = this.cache;

    this.endpoint = endpoint ?? { host: 'localhost', port: 7007 };
  }

  async _call(func: string, args: JsonMap, group?: GroupCall) {
    if (group) {
      return await group._group_call(this.#client, func, args);
    }

    global.app.log.d('calling', func, args);

    const data = await this.#client
      .send([
        {
          fname: func,
          ...args,
        },
      ])
      .then((d) => {
        global.app.log.d(func, 'received data');
        throw_msg_error(d);
        return d?.data?.[0];
      });

    return data;
  }

  get logged_in() {
    return this.#client._accepted;
  }

  status() {
    return {
      loggedIn: this.logged_in,
      connected: this.#client.is_connected(),
    };
  }

  create_group_call() {
    return new GroupCall();
  }

  async properties<
    K extends (
      | 'version'
      | 'user'
      | 'state'
      | 'update'
      | 'guest_allowed'
      | 'no_namespace_key'
      | 'webserver'
      | 'webserver.host'
      | 'webserver.port'
      | 'webserver.ssl'
      | 'pixie'
      | 'pixie.connect'
    )[]
  >(
    args: {
      keys: K;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_properties', args, group);
    throw_msg_error(data);
    return data.data as Record<Unwrap<K>, any>;
  }

  async login(
    user?: string,
    password?: string,
    endpoint?: { host: string; port: number }
  ) {
    if (endpoint) {
      if (
        this.#client.is_connected() &&
        (endpoint.host !== this.endpoint.host ||
          endpoint.port !== this.endpoint.port)
      ) {
        global.app.log.i(
          'New HPX server endpoint specificed while old connection exists, closing old connection'
        );
        this.#client.close();
      }
      this.endpoint = endpoint;
    }

    if (!this.#client.is_connected()) {
      await this.#client.connect(this.endpoint);
    }

    const r = await this.#client
      .request_auth()
      .then((m) => this.#client.handshake({ user, password }));
    return r;
  }

  async config(
    args: {
      cfg: Record<string, AnyJson>;
      flatten?: boolean;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_config', args, group);
    throw_msg_error(data);
    return data.data as JsonMap;
  }

  async set_config(
    args: {
      cfg: Record<string, AnyJson>;
    },
    group?: GroupCall
  ) {
    const data = await this._call('set_config', args, group);
    throw_msg_error(data);
    return data.data as AnyJson;
  }

  async update_item<R = undefined>(
    args: {
      item_type: ItemType;
      item: Record<string, AnyJson>;
      options?: JsonMap;
    },
    group?: GroupCall
  ) {
    const data = await this._call('update_item', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async update_metatags<R = undefined>(
    args: {
      item_type: ItemType;
      item_id: number | number[];
      metatags: Partial<Omit<ServerMetaTags, keyof ServerItem>>;
    },
    group?: GroupCall
  ) {
    const data = await this._call('update_metatags', args, group);
    throw_msg_error(data);
    return data.data as boolean | number;
  }

  async item<R = undefined>(
    args: {
      item_type: ItemType;
      item_id: number | number[];
      fields?: FieldPath[];
      profile_options?: ProfileOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_item', args, group);
    throw_msg_error(data);
    return data.data as R extends undefined ? JsonMap : R;
  }

  async items<R = undefined>(
    args: {
      item_type: ItemType;
      fields?: FieldPath[];
      offset?: number;
      limit?: number;
      metatags?: Partial<Omit<ServerMetaTags, keyof ServerItem>>;
      profile_options?: ProfileOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_items', args, group);
    throw_msg_error(data);
    return data.data as {
      count: number;
      items: R extends undefined ? JsonMap[] : R[];
    };
  }

  async search_items<R = undefined>(
    args: {
      item_type: ItemType;
      fields?: FieldPath[];
      offset?: number;
      limit?: number;
      search_query?: string;
      search_options?: SearchOptions;
      sort_options?: SortOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('search_items', args, group);
    throw_msg_error(data);
    return data.data as {
      count: number;
      items: R extends undefined ? JsonMap[] : R[];
    };
  }

  async related_items<R = undefined>(
    args: {
      item_type: ItemType;
      item_id: number | number[];
      related_type: ItemType;
      fields?: FieldPath[];
      offset?: number;
      metatags?: Partial<Omit<ServerMetaTags, keyof ServerItem>>;
      limit?: number;
      profile_options?: ProfileOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_related_items', args, group);
    throw_msg_error(data);
    return data.data as {
      count: number;
      items: R extends undefined ? JsonMap[] : R[];
    };
  }

  async from_grouping(
    args: {
      gallery_id?: number;
      grouping_id?: number;
      number?: number;
      prev?: boolean;
      fields?: FieldPath[];
      profile_options?: ProfileOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_from_grouping', args, group);
    throw_msg_error(data);
    return data.data as null | ServerGallery;
  }

  async open_gallery(
    args: {
      item_id: number;
      item_type: ItemType;
      viewer_args?: string;
    },
    group?: GroupCall
  ) {
    const data = await this._call('open_gallery', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async pages(
    args: {
      gallery_id: number;
      number?: number;
      window_size?: number;
      fields?: FieldPath[];
      profile_options?: ProfileOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_pages', args, group);
    throw_msg_error(data);
    return data.data as {
      count: number;
      items: PartialExcept<ServerPage, 'id'>[];
    };
  }

  async profile(
    args: {
      item_type: ItemType;
      item_ids: number[];
      profile_options?: ProfileOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_profile', args, group);
    throw_msg_error(data);
    return data.data as { [key: string]: number };
  }

  async library<R = undefined>(
    args: {
      item_type: ItemType;
      item_id?: number;
      related_type?: ItemType;
      fields?: FieldPath<R>[];
      page?: number;
      limit?: number;
      metatags?: Partial<Omit<ServerMetaTags, keyof ServerItem>>;
      filter_id?: number;
      sort_options?: SortOptions;
      search_query?: string;
      search_options?: SearchOptions;
      profile_options?: ProfileOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('library_view', args, group);
    throw_msg_error(data);
    return data.data as {
      count: number;
      items: R extends undefined ? JsonMap[] : R[];
    };
  }

  async similar<R = undefined>(
    args: {
      item_type: ItemType;
      item_id: number;
      fields?: FieldPath<R>[];
      limit?: number;
      profile_options?: ProfileOptions;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_similar', args, group);
    throw_msg_error(data);
    return data.data as CommandID<{
      count: number;
      items: R extends undefined ? JsonMap[] : R[];
    }>;
  }

  async update_filters(
    args: {
      item_ids: number[];
    },
    group?: GroupCall
  ) {
    const data = await this._call('update_filters', args, group);
    throw_msg_error(data);
    return data.data as CommandID<boolean>;
  }

  async search_labels(
    args: {
      item_types: ItemType[];
      search_query: string;
      limit?: number;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_search_labels', args, group);
    throw_msg_error(data);
    return data.data as {
      count: number;
      items: SearchItem[];
    };
  }

  async sort_indexes(
    args: {
      item_type: ItemType;
      translate?: boolean;
      children?: boolean;
      locale?: string;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_sort_indexes', args, group);
    throw_msg_error(data);
    return data.data as ServerSortIndex[];
  }

  async log(args: { log_type: LogType }, group?: GroupCall) {
    const data = await this._call('get_log', args, group);
    throw_msg_error(data);
    return data.data as { log: string };
  }

  async download_info(args: {}, group?: GroupCall) {
    const data = await this._call('get_download_info', args, group);
    throw_msg_error(data);
    return data.data as DownloadHandler[];
  }

  async metadata_info(args: {}, group?: GroupCall) {
    const data = await this._call('get_metadata_info', args, group);
    throw_msg_error(data);
    return data.data as MetadataHandler[];
  }

  async add_items_to_metadata_queue(
    args: {
      items_kind: ItemsKind;
      item_type?: ItemType;
      options?: {};
      priority?: Priority;
    },
    group?: GroupCall
  ) {
    const data = await this._call('add_items_to_metadata_queue', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async add_urls_to_download_queue(
    args: {
      urls: string[];
      identifier?: string[];
      options?: {};
      priority?: Priority;
    },
    group?: GroupCall
  ) {
    const data = await this._call('add_urls_to_download_queue', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async add_item_to_queue(
    args: {
      item_id: number | number[];
      item_type?: ItemType;
      queue_type: QueueType;
      options?: {};
      priority?: Priority;
    },
    group?: GroupCall
  ) {
    const data = await this._call('add_item_to_queue', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async remove_item_from_queue(
    args: {
      item_id: number;
      item_type?: ItemType;
      queue_type: QueueType;
    },
    group?: GroupCall
  ) {
    const data = await this._call('remove_item_from_queue', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async stop_queue(args: { queue_type: QueueType }, group?: GroupCall) {
    const data = await this._call('stop_queue', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async start_queue(args: { queue_type: QueueType }, group?: GroupCall) {
    const data = await this._call('start_queue', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async clear_queue(args: { queue_type: QueueType }, group?: GroupCall) {
    const data = await this._call('clear_queue', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }

  async queue_state<T extends QueueType>(
    args: { queue_type: T; include_finished?: boolean },
    group?: GroupCall
  ) {
    const data = await this._call('get_queue_state', args, group);
    throw_msg_error(data);

    type D = T extends QueueType.Metadata ? MetadataItem[] : DownloadItem[];

    return data.data as {
      size: number;
      value: number;
      percent: number;
      active: D;
      finished: D;
      running: boolean;
    };
  }

  async queue_items<T extends QueueType>(
    args: {
      limit?: number;
      queue_type: T;
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_queue_items', args, group);
    throw_msg_error(data);
    return data.data as T extends QueueType.Metadata
      ? MetadataItem[]
      : DownloadItem[];
  }

  async start_command(args: { command_ids: string[] }, group?: GroupCall) {
    const data = await this._call('start_command', args, group);
    throw_msg_error(data);
    return data.data as Record<CommandIDKey, CommandState>;
  }

  async stop_command(args: { command_ids: string[] }, group?: GroupCall) {
    const data = await this._call('stop_command', args, group);
    throw_msg_error(data);
    return data.data as Record<CommandIDKey, CommandState>;
  }

  async command_state(args: { command_ids: string[] }, group?: GroupCall) {
    const data = await this._call('get_command_state', args, group);
    throw_msg_error(data);
    return data.data as Record<CommandIDKey, CommandState>;
  }

  async command_value<R = AnyJson>(
    args: { command_ids: string[] },
    group?: GroupCall
  ) {
    const data = await this._call('get_command_value', args, group);
    throw_msg_error(data);
    return data.data as Record<CommandIDKey, R>;
  }

  async command_progress(args: { command_ids: string[] }, group?: GroupCall) {
    const data = await this._call('get_command_progress', args, group);
    throw_msg_error(data);
    return data.data as
      | Record<CommandIDKey, CommandProgress>
      | CommandProgress[];
  }

  async list_plugins(args: { state?: PluginState }, group?: GroupCall) {
    const data = await this._call('list_plugins', args, group);
    throw_msg_error(data);
    return data.data as PluginData[];
  }

  async plugin(args: { plugin_id: string }, group?: GroupCall) {
    const data = await this._call('get_plugin', args, group);
    throw_msg_error(data);
    return data.data as PluginData;
  }

  async install_plugin(args: { plugin_id: string }, group?: GroupCall) {
    const data = await this._call('install_plugin', args, group);
    throw_msg_error(data);
    return data.data as PluginState;
  }

  async disable_plugin(args: { plugin_id: string }, group?: GroupCall) {
    const data = await this._call('disable_plugin', args, group);
    throw_msg_error(data);
    return data.data as PluginState;
  }

  async remove_plugin(args: { plugin_id: string }, group?: GroupCall) {
    const data = await this._call('remove_plugin', args, group);
    throw_msg_error(data);
    return data.data as PluginState;
  }

  async check_plugin_update(
    args: { plugin_ids?: string[]; force?: boolean; push?: boolean },
    group?: GroupCall
  ) {
    const data = await this._call('check_plugin_update', args, group);
    throw_msg_error(data);
    return data.data as CommandID<{
      plugin_id: string;
      url: string;
      version: Version;
    }>;
  }

  async update_plugin(
    args: { plugin_ids?: string[]; force?: boolean; push?: boolean },
    group?: GroupCall
  ) {
    const data = await this._call('update_plugin', args, group);
    throw_msg_error(data);
    return data.data as CommandID<string[]>;
  }

  async send_plugin_message(
    args: { plugin_id?: string; msg: AnyJson },
    group?: GroupCall
  ) {
    const data = await this._call('send_plugin_message', args, group);
    throw_msg_error(data);
    return data.data as AnyJson;
  }

  async submit_login(
    args: { identifier?: string; credentials: JsonMap; options?: JsonMap },
    group?: GroupCall
  ) {
    const data = await this._call('submit_login', args, group);
    throw_msg_error(data);
    return data.data as CommandID<{
      status: string;
      logged_in: boolean;
    }>;
  }

  async page_read_event(args: { item_id: number }, group?: GroupCall) {
    const data = await this._call('page_read_event', args, group);
    throw_msg_error(data);
    return data.data as boolean;
  }
}

function throw_msg_error(msg: ServerMsg) {
  if (msg.error) {
    const msgerror: ServerErrorMsg = msg.error;
    const err = Error(`${msgerror.code}: ${msgerror.msg}`);
    err.data = msg;
    err.code = msgerror.code;
    global.app.log.e(err);

    throw err;
  }
}

const timeoutError = Symbol();

function promiseTimeout(
  prom: Promise<any>,
  time: number,
  exception: any = timeoutError
) {
  let timer;
  return Promise.race([
    prom,
    new Promise((_r, rej) => (timer = setTimeout(rej, time, exception))),
  ]).finally(() => clearTimeout(timer));
}
export class GroupCall {
  #client: Client;
  #functions: {
    name: string;
    args: JsonMap;
  }[];
  #promises_resolves: [
    resolve: (value: unknown) => void,
    reject: (reason: any) => void
  ][];
  #promises: Promise<any>[];

  #resolved;

  constructor() {
    this.#resolved = false;
    this.#promises_resolves = [];
    this.#functions = [];
    this.#promises = [];
  }

  _group_call(client: Client, func: string, args: JsonMap) {
    if (this.#resolved) {
      throw Error('Group call already resolved');
    }
    this.#client = client;
    this.#functions.push({
      name: func,
      args,
    });

    const p = new Promise((resolve, reject) => {
      this.#promises_resolves.push([resolve, reject]);
    });

    this.#promises.push(p);

    promiseTimeout(p, 10000).catch((e) => {
      if (e === timeoutError) {
        global.app.log.c("forgot to call 'GroupCall.call()' for: ", func);
        this.#promises_resolves.forEach(([_, reject]) => reject(e));
      } else {
        global.app.log.e(e);
      }
    });

    return p;
  }

  async call(opt?: { throw_error?: boolean }) {
    try {
      if (this.#resolved) {
        throw Error('Group call already resolved');
      }
      this.#resolved = true;
      global.app.log.d('group calling', this.#functions.length, 'functions');
      const data = await this.#client.send(
        this.#functions.map((f) => {
          return {
            fname: f.name,
            ...f.args,
          };
        })
      );

      global.app.log.d(
        'group calling',
        this.#functions.length,
        'functions received data'
      );

      throw_msg_error(data);
      (data?.data as JsonArray)?.forEach?.((r, idx) => {
        this.#promises_resolves[idx][0](r);
      });
      await Promise.allSettled(this.#promises);
      return true;
    } catch (err) {
      this.#promises_resolves.forEach(([_, reject]) => reject(err));
      await Promise.allSettled(this.#promises);
      if (opt?.throw_error !== false) {
        throw err;
      }
      return false;
    }
  }
}
