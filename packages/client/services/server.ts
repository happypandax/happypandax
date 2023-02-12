import EventEmitter from 'events';
import Client, {
  AnyJson,
  AuthError,
  exception_codes,
  JsonMap,
  log,
  ServerDisconnectError,
  ServerErrorMsg,
  ServerFunctionMsg,
  ServerMsg,
} from 'happypandax-client';

import { QueryClient, QueryFunctionContext } from '@tanstack/query-core';

import { ServiceType } from '../server/constants';
import { getServerSession } from '../server/requests';
import {
  ActivityType,
  CommandState,
  ItemsKind,
  ItemType,
  LogType,
  PluginState,
  Priority,
  QueueType,
  TransientViewAction,
  TransientViewType,
} from '../shared/enums';
import {
  Activity,
  CommandID,
  CommandIDKey,
  CommandProgress,
  DownloadHandler,
  DownloadItem,
  FieldPath,
  FileViewItem,
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
  ServerUser,
  SortOptions,
  Version,
  ViewID,
} from '../shared/types';
import { Service } from './base';

// We are going to create multiple clients to support parallel requests, HPX supports this
enum ClientType {
  /**
   * main client, used for most requests
   */
  main,
  /**
   * background client, used for long running requests
   */
  background,
  /**
   * poll client, used for poll requests
   */
  poll,
}

export interface CallOptions {
  client?: ClientType;
  cache?: boolean;
  invalidate?: boolean;
  ignoreError?: boolean;
}

const cacheTime = 1000 * 60 * 60 * 6; // 6 hours

class ClientCluster {
  public main: Client;
  public background: Client;
  public poll: Client;

  constructor(main: Client, background: Client, poll: Client) {
    this.main = main;
    this.background = background;
    this.poll = poll;
  }

  get(client: ClientType) {
    switch (client) {
      case ClientType.main:
        return this.main;
      case ClientType.background:
        return this.background;
      case ClientType.poll:
        return this.poll;
      default:
        throw new Error('Invalid client type');
    }
  }
}

export interface Endpoint {
  host: string;
  port: number;
}

export default class ServerService extends Service {
  endpoint: Endpoint;

  #clients: Record<ClientType, Client>;
  #main_client: Client;
  #emitter: EventEmitter = new EventEmitter();

  // intentionally not using a private field here
  private _disconnect_listener: () => void;

  #servers = new Map<string, Server>();
  #sessions: Set<string> = global.app.hpx_sessions ?? new Set();

  constructor(endpoint?: Endpoint) {
    super(ServiceType.Server);

    global.app.hpx_sessions = this.#sessions

    const client_name = 'next-client';

    log.enabled = false;
    log.logger = {
      debug: global.app.log.d,
      info: global.app.log.i,
      warning: global.app.log.w,
      error: global.app.log.e,
    };

    this.endpoint = endpoint ?? { host: 'localhost', port: 7007 };

    // this avoiding recreating the hpx client during HMR
    this.#clients = global.app?.hpx_clients ?? {
      [ClientType.main]: new Client({ name: client_name }),
      [ClientType.background]: new Client({
        name: client_name + '#background',
      }),
      [ClientType.poll]: new Client({ name: client_name + '#poll' }),
    };
    global.app.hpx_clients = this.#clients;
    this.#main_client = this.#clients[ClientType.main];

    this._disconnect_listener = () => {
      this.emit('disconnect', this.endpoint);
    }

    this.on('disconnect', () => this._on_disconnect());

  }

  private _on_disconnect() {
    this.#sessions.clear();
    global.app.hpx_sessions = this.#sessions;
    this.#servers.clear();
    this.#sessions.clear();
  }

  off(event: string, listener: (...args: any[]) => void): this {
    this.#emitter.off(event, listener);
    return this;
  }

  on(event: 'disconnect', listener: (endpoint: Endpoint) => void): this
  on(event: 'connect', listener: (endpoint: Endpoint) => void): this
  on(event: 'login', listener: (endpoint: Endpoint, session: string) => void): this
  on(event: 'logout', listener: (endpoint: Endpoint, session: string) => void): this
  on(event: string, listener: (...args: any[]) => void): this {
    this.#emitter.on(event, listener);
    return this;
  }

  emit(event: 'disconnect', endpoint: Endpoint): void;
  emit(event: 'connect', endpoint: Endpoint): void;
  emit(event: 'login', endpoint: Endpoint, session: string): void;
  emit(event: 'logout', endpoint: Endpoint, session: string): void;
  emit(event: string, ...args: any[]) {
    this.#emitter.emit(event, ...args);
  }

  private _close_clients() {
    for (const client of Object.values(this.#clients)) {
      client.close();
      client.off('close', this._disconnect_listener);
    }
  }

  async connect(endpoint?: { host: string; port: number }) {
    if (this.#main_client.is_connected()) {

      if ((endpoint.host === this.endpoint.host && endpoint.port == this.endpoint.port)) {
        global.app.log.i("Already connected to HPX server at " + this.endpoint.host + ":" + this.endpoint.port)
        return;
      } else {
        global.app.log.i(
          'New HPX server endpoint specificed while old connection exists, closing old connection'
        );
        this._close_clients();
      }
    }

    global.app.log.i("Connecting to HPX server... at " + this.endpoint.host + ":" + this.endpoint.port)

    if (!this.#main_client.is_connected()) {
      for (const client of Object.values(this.#clients)) {
        await client.connect(this.endpoint);
      }

      this.#main_client.on('close', this._disconnect_listener);

    }

    this.emit('connect', this.endpoint);

    this.endpoint = endpoint;
  }

  async login(
    user?: string,
    password?: string,

  ) {
    global.app.log.d("Logging in to HPX server... at " + this.endpoint.host + ":" + this.endpoint.port)

    const s = await this.#main_client.handshake({ user, password });
    if (s) {
      const session = this.#main_client.session
      this._create_server(session);
      // link the others
      for (const client of Object.values(this.#clients)) {
        if (client != this.#main_client) {
          client.session = session;
        }
      }

      this.emit('login', this.endpoint, session)
      return session
    }
    return undefined;
  }

  async logout(session: string) {
    const server = this.#servers.get(session);
    if (server) {
      global.app.log.d("Logging out of HPX server... at " + this.endpoint.host + ":" + this.endpoint.port)
      this.#main_client.session = session;
      await this.#main_client.drop_auth();
      const server = this.session(session);
      if (server) {
        server.accepted = false;
      }
      this.#servers.delete(session);
      this.#sessions.delete(session);
      this.emit('logout', this.endpoint, session)
      global.app.log.d("Successfully logged out of HPX server at " + this.endpoint.host + ":" + this.endpoint.port, ' (', session, ')')
      return true
    }
    global.app.log.d("Failed to log out of HPX server at " + this.endpoint.host + ":" + this.endpoint.port, ' because of invalid session (', session, ')')
    return false
  }

  private _create_server(session: string) {
    const server = new Server(session);
    server.accepted = true;
    this.#servers.set(session, server);
    if (!this.#sessions.has(session)) {
      this.#sessions.add(session);
    }
    return server;
  }

  get clients() {
    return [this.#main_client];
  }

  is_connected() {
    return this.#main_client.is_connected();
  }

  session(session: string) {
    // This supports HMR
    if (process.env.NODE_ENV === 'development' && this.#sessions.has(session) && !this.#servers.has(session)) {
      this._create_server(session);
      this.emit('login', this.endpoint, session)
    }

    if (!this.is_connected()) {
      return undefined;
    }

    return this.#servers.get(session) as Server | undefined;
  }

  async context(...params: Parameters<typeof getServerSession>) {
    const s = await getServerSession(...params);
    if (!s) {
      return undefined;
    }
    return this.session(s.id);
  }
}

export class Server {

  public session: string;
  accepted = false;

  query_client: QueryClient;

  #clients: Record<ClientType, Client>;


  constructor(session: string) {
    this.session = session;

    const client_name = 'next-client';

    // this.#pool = global.app?.hpx_pool ?? GenericPool.createPool({
    //   async create() {
    //     return new ClientCluster(
    //       new Client({ name: client_name }),
    //       new Client({ name: client_name + '#background' }),
    //       new Client({ name: client_name + '#poll' })
    //     );
    //   },
    //   async destroy(client) {
    //     await client.main.close();
    //     await client.background.close();
    //     await client.poll.close();
    //   }
    // }, {
    //   max: 10,
    //   min: 1,
    // })

    // global.app.hpx_pool = this.#pool;

    // this avoiding recreating the hpx client during HMR
    this.#clients = global.app?.hpx_clients ?? {
      [ClientType.main]: new Client({ name: client_name }),
      [ClientType.background]: new Client({
        name: client_name + '#background',
      }),
      [ClientType.poll]: new Client({ name: client_name + '#poll' }),
    };
    global.app.hpx_clients = this.#clients;

    this.query_client = new QueryClient({
      defaultOptions: {
        mutations: {
          retry: () => false,
        },
        queries: {
          retry: () => false,
          networkMode: 'always',
          staleTime: cacheTime * 2,
          cacheTime: cacheTime,
        },
      },
    });
  }

  async _call(
    func: string,
    args: JsonMap,
    group?: GroupCall,
    options?: CallOptions
  ) {
    try {
      const client_type = options?.client ?? ClientType.main;

      const client = this.#clients[client_type];
      if (!client) {
        throw Error(`Invalid client from type ${client_type}`);
      }

      if (group) {
        return await group._group_call(
          this,
          this.query_client,
          client,
          func,
          args,
          options
        );
      }

      const r = await queryClientFetchQuery(
        this.session,
        this.query_client,
        client,
        [[func, args]],
        options
      );

      const data = r?.data?.[0];

      throw_msg_error(data, options);

      global.app.log.d('HPX call', func, args, '->', data)

      return data;
    } catch (e) {
      if (e instanceof AuthError || [
        exception_codes.AuthError,
        exception_codes.AuthMissingCredentials,
        exception_codes.AuthRequiredError,
        exception_codes.AuthWrongCredentialsError].includes(e?.code)) {
        this.accepted = false;
      }
      throw e
    }
  }

  get logged_in() {
    return this.accepted;
  }


  create_group_call() {
    return new GroupCall();
  }

  async properties<
    K extends {
      version: any,
      user: any,
      state: any,
      update: any,
      guest_allowed: any,
      no_namespace_key: any,
      webserver: {
        host: any,
        port: any,
        ssl: any,
      },
      pixie: {
        connect: any,
      },
    },
    P extends DeepPickPathPlain<K>
  >(
    args: {
      keys: P[];
    },
    group?: GroupCall
  ) {
    const data = await this._call('get_properties', args, group);
    return data.data as DeepPick<K, P>;
  }

  async user(args: {}, group?: GroupCall, options?: CallOptions) {
    const data = await this._call('get_user', args, group, options);

    return data.data as ServerUser;
  }

  async config(
    args: {
      cfg: Record<string, AnyJson>;
      flatten?: boolean;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_config', args, group, options);

    return data.data as JsonMap;
  }

  async set_config(
    args: {
      cfg: Record<string, AnyJson>;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('set_config', args, group, options);

    return data.data as AnyJson;
  }

  async update_item<R = undefined>(
    args: {
      item_type: ItemType;
      item: Record<string, AnyJson>;
      options?: JsonMap;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('update_item', args, group, {
      invalidate: true,
      ...options,
    });

    return data.data as boolean;
  }

  async update_metatags<R = undefined>(
    args: {
      item_type: ItemType;
      item_id: number | number[];
      metatags: Partial<Omit<ServerMetaTags, keyof ServerItem>>;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('update_metatags', args, group, {
      invalidate: true,
      ...options,
    });

    return data.data as boolean | number;
  }

  async item<R = undefined>(
    args: {
      item_type: ItemType;
      item_id: number | number[];
      fields?: FieldPath[];
      profile_options?: ProfileOptions;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_item', args, group, {
      cache: true,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_items', args, group, {
      cache: true,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('search_items', args, group, {
      cache: true,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_related_items', args, group, {
      cache: true,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_from_grouping', args, group, {
      cache: true,
      ...options,
    });

    return data.data as null | ServerGallery;
  }

  async open_gallery(
    args: {
      item_id: number;
      item_type: ItemType;
      viewer_args?: string;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('open_gallery', args, group, options);

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_pages', args, group, {
      cache: true,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_profile', args, group, {
      cache: true,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('library_view', args, group, {
      cache: true,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_similar', args, group, {
      cache: true,
      ...options,
    });

    return data.data as CommandID<{
      count: number;
      items: R extends undefined ? JsonMap[] : R[];
    }>;
  }

  async update_filters(
    args: {
      item_ids: number[];
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('update_filters', args, group, {
      invalidate: true,
      ...options,
    });

    return data.data as CommandID<boolean>;
  }

  async search_labels(
    args: {
      item_types: ItemType[];
      search_query: string;
      limit?: number;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_search_labels', args, group, {
      cache: true,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_sort_indexes', args, group, {
      cache: true,
      ...options,
    });

    return data.data as ServerSortIndex[];
  }

  async log(
    args: { log_type: LogType },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_log', args, group, {
      client: ClientType.poll,
      ...options,
    });

    return data.data as { log: string };
  }

  async download_info(args: {}, group?: GroupCall, options?: CallOptions) {
    const data = await this._call('get_download_info', args, group, options);

    return data.data as DownloadHandler[];
  }

  async metadata_info(args: {}, group?: GroupCall, options?: CallOptions) {
    const data = await this._call('get_metadata_info', args, group, options);

    return data.data as MetadataHandler[];
  }

  async add_items_to_metadata_queue(
    args: {
      items_kind: ItemsKind;
      item_type?: ItemType;
      options?: {};
      priority?: Priority;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('add_items_to_metadata_queue', args, group, {
      client: ClientType.background,
      ...options,
    });

    return data.data as boolean;
  }

  async add_urls_to_download_queue(
    args: {
      urls: string[];
      identifier?: string[];
      options?: {};
      priority?: Priority;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('add_urls_to_download_queue', args, group, {
      client: ClientType.background,
      ...options,
    });

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
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('add_item_to_queue', args, group, {
      client: ClientType.background,
      ...options,
    });

    return data.data as boolean;
  }

  async remove_item_from_queue(
    args: {
      item_id: number;
      item_type?: ItemType;
      queue_type: QueueType;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call(
      'remove_item_from_queue',
      args,
      group,
      options
    );

    return data.data as boolean;
  }

  async stop_queue(
    args: { queue_type: QueueType },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('stop_queue', args, group, options);

    return data.data as boolean;
  }

  async start_queue(
    args: { queue_type: QueueType },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('start_queue', args, group, options);

    return data.data as boolean;
  }

  async clear_queue(
    args: { queue_type: QueueType },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('clear_queue', args, group, {
      client: ClientType.background,
      ...options,
    });

    return data.data as boolean;
  }

  async queue_state<T extends QueueType>(
    args: {
      queue_type: T;
      include_finished?: boolean;
      include_queued?: boolean;
      include_active?: boolean;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_queue_state', args, group, {
      client: ClientType.poll,
      ...options,
    });


    type D = T extends QueueType.Metadata ? MetadataItem[] : DownloadItem[];

    return data.data as {
      active_size: number;
      queued_size: number;
      size: number;
      value: number;
      percent: number;
      active: D;
      finished: D;
      queued: D;
      running: boolean;
      session: {
        queued: number;
        finished: number;
        active: number;
        total: number;
        start_time: number;
        end_time: number;
      };
    };
  }

  async queue_items<T extends QueueType>(
    args: {
      limit?: number;
      include_finished?: boolean;
      include_queued?: boolean;
      include_active?: boolean;
      queue_type: T;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_queue_items', args, group, options);


    type D = T extends QueueType.Metadata ? MetadataItem[] : DownloadItem[];

    return data.data as {
      active_size: number;
      queued_size: number;
      size: number;
      active: D;
      finished: D;
      queued: D;
    };
  }

  async start_command(
    args: { command_ids: string[] },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('start_command', args, group, options);

    return data.data as Record<CommandIDKey, CommandState>;
  }

  async stop_command(
    args: { command_ids: string[] },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('stop_command', args, group, options);

    return data.data as Record<CommandIDKey, CommandState>;
  }

  async command_state(
    args: { command_ids: string[] },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_command_state', args, group, {
      client: ClientType.poll,
      ...options,
    });

    return data.data as Record<CommandIDKey, CommandState>;
  }

  async command_value<R = AnyJson>(
    args: { command_ids: string[] },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_command_value', args, group, options);

    return data.data as Record<CommandIDKey, R>;
  }

  async command_progress(
    args: { command_ids: string[] },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_command_progress', args, group, {
      client: ClientType.poll,
      ...options,
    });

    return data.data as
      | Record<CommandIDKey, CommandProgress>
      | CommandProgress[];
  }

  async activities(
    args: { items: Record<string, number[]>; activity_type?: ActivityType },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_activities', args, group, {
      client: ClientType.background,
      ...options,
    });

    return data.data as Record<string, Record<string, Activity[]>>;
  }

  async list_plugins(
    args: { state?: PluginState },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('list_plugins', args, group, options);

    return data.data as PluginData[];
  }

  async plugin(
    args: { plugin_id: string },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_plugin', args, group, options);

    return data.data as PluginData;
  }

  async install_plugin(
    args: { plugin_id: string },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('install_plugin', args, group, {
      ...options,
    });

    return data.data as PluginState;
  }

  async disable_plugin(
    args: { plugin_id: string },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('disable_plugin', args, group, {
      ...options,
    });

    return data.data as PluginState;
  }

  async remove_plugin(
    args: { plugin_id: string },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('remove_plugin', args, group, { ...options });

    return data.data as PluginState;
  }

  async check_plugin_update(
    args: { plugin_ids?: string[]; force?: boolean; push?: boolean },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('check_plugin_update', args, group, {
      client: ClientType.poll,
      ...options,
    });

    return data.data as CommandID<{
      plugin_id: string;
      url: string;
      version: Version;
    }>;
  }

  async update_plugin(
    args: { plugin_ids?: string[]; force?: boolean; push?: boolean },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('update_plugin', args, group, { ...options });

    return data.data as CommandID<string[]>;
  }

  async send_plugin_message(
    args: { plugin_id?: string; msg: AnyJson },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('send_plugin_message', args, group, options);

    return data.data as AnyJson;
  }

  async submit_login(
    args: { identifier?: string; credentials: JsonMap; options?: JsonMap },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('submit_login', args, group, options);

    return data.data as CommandID<{
      status: string;
      logged_in: boolean;
    }>;
  }

  async page_read_event(
    args: { item_id: number },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('page_read_event', args, group, {
      invalidate: true,
      ...options,
    });

    return data.data as boolean;
  }

  async resolve_path_pattern(
    args: { pattern: string },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('resolve_path_pattern', args, group, {
      ...options,
    });

    return data.data as (
      | string
      | {
        class: string;
        start: number;
        end: number;
        text: string;
        token: string;
        type: string;
        error: string;
      }
    )[];
  }

  async scan_galleries(
    args: {
      path: string;
      patterns?: string[];
      options?: {};
      view_id?: ViewID;
      limit?: number;
      offset?: number;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('scan_galleries', args, group, {
      ...options,
    });

    return data.data as {
      command_id: string;
      view_id: string;
    };
  }

  async transient_view<T extends TransientViewType>(
    args: {
      view_id: ViewID;
      desc?: boolean;
      limit?: number;
      offset?: number;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('transient_view', args, group, {
      ...options,
    });

    return data.data as {
      id: ViewID;
      timestamp: number;
      type: TransientViewType;
      options: {};
      count: number;
      state: CommandState;
      properties: JsonMap;
      roots: string[];
      items: (T extends TransientViewType.File ? FileViewItem : never)[];
      progress: CommandProgress;
    };
  }

  async transient_view_action(
    args: {
      view_id: ViewID;
      action: TransientViewAction;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('transient_view_action', args, group, {
      ...options,
    });

    return data.data as CommandID<boolean>;
  }

  async transient_views(
    args: {
      view_type?: TransientViewType;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('transient_views', args, group, {
      ...options,
    });

    return data.data as {
      id: ViewID;
      timestamp: number;
      state: CommandState;
      type: TransientViewType;
      count: number;
    }[];
  }
}

function clientCall(ctx: QueryFunctionContext) {
  const session = ctx.meta.session as string;
  const client = ctx.meta.client as Client;
  const calls = ctx.meta.calls as [fname: string, args: JsonMap][];
  const fnames = calls.map((v) => v[0]);

  global.app.log.d('calling', ...calls.flat());

  client.session = session;
  return client
    .send('call',
      calls.map((c) => ({
        fname: c[0],
        ...c[1],
      }))
    )
    .then((d) => {
      global.app.log.d(fnames, 'received data');
      throw_msg_error(d);
      return d;
    })
    .catch((e) => {
      if (
        e instanceof ServerDisconnectError ||
        e.message.includes('not connected')
      ) {
        const fairy = global.app.service.get(ServiceType.Fairy);
        fairy.healthcheck();
      }

      throw e;
    });
}

async function queryClientFetchQuery(
  session: string,
  query_client: QueryClient,
  client: Client,
  calls: [fname: string, args: JsonMap][],
  call_options?: CallOptions
) {
  if (call_options?.invalidate) {
    const fnames = calls.map((v) => v[0]);
    global.log.d('invalidating cache by', ...fnames);
    await query_client.invalidateQueries();
  }

  const key = calls.flat();
  return query_client.fetchQuery(key, clientCall, {
    cacheTime: !call_options?.cache ? 0 : cacheTime,
    meta: {
      session,
      client,
      calls,
    },
  });
}

function throw_msg_error(msg: ServerMsg<any> | ServerFunctionMsg, options?: CallOptions) {
  if (msg?.error && !options?.ignoreError) {
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
  server?: Server;
  #client: Client;
  #query_client: QueryClient;
  #options: CallOptions;
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
    this.#options = {};
  }

  _group_call(
    server: Server,
    query_client: QueryClient,
    client: Client,
    func: string,
    args: JsonMap,
    options?: CallOptions
  ) {
    if (this.#resolved) {
      throw Error('Group call already resolved');
    }
    this.server = server;
    this.#client = client;
    this.#query_client = query_client;
    this.#functions.push({
      name: func,
      args,
    });

    if (this.#options.cache === undefined) {
      this.#options.cache = options?.cache;
    } else if (options.cache) {
      if (this.#options.cache !== false) {
        this.#options.cache = options.cache;
      }
    } else {
      this.#options.cache = options?.cache;
    }

    if (this.#options.invalidate === undefined) {
      this.#options.invalidate = options?.invalidate;
    } else if (options.invalidate) {
      if (this.#options.invalidate !== false) {
        this.#options.invalidate = options.invalidate;
      }
    } else {
      this.#options.invalidate = options?.invalidate;
    }

    const p = new Promise<ServerFunctionMsg>((resolve, reject) => {
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
      if (!this.server) {
        throw Error('No server associated with group');
      }
      if (this.#resolved) {
        throw Error('Group call already resolved');
      }
      this.#resolved = true;

      const data = await queryClientFetchQuery(
        this.server.session,
        this.#query_client,
        this.#client,
        this.#functions.map((f) => [f.name, f.args]),
        this.#options
      );

      throw_msg_error(data);
      data?.data?.forEach?.((r, idx) => {
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
