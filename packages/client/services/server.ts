import EventEmitter from 'events';
import GenericPool from 'generic-pool';
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
  ApplicationState,
  CommandState,
  ItemsKind,
  ItemType,
  LogType,
  PluginState,
  Priority,
  QueueType,
  TransientViewAction,
  TransientViewSubmitAction,
  TransientViewType,
} from '../shared/enums';
import { CancelledError } from '../shared/error';
import {
  Activity,
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
  ServerUser,
  SortOptions,
  TransientView,
  Version,
  ViewID,
} from '../shared/types';
import { Service, ServiceLocator } from './base';

const CLIENT_POOL_SIZE = 25;
const CLIENT_NAME =
  process.env.NODE_ENV === 'production' ? 'webclient' : 'next-client';

// We are going to create multiple clients to support parallel requests, HPX supports this
enum ClientType {
  /**
   * main client, used for most requests
   */
  main = 'main',
  /**
   * background client, used for long running requests
   */
  background = 'background',
  /**
   * poll client, used for poll requests
   */
  poll = 'poll',
}

enum PoolPriority {
  HIGH = 0,
  MEDIUM = 1,
  LOW = 2,
}

export interface CallOptions {
  client?: ClientType;
  cache?: boolean;
  invalidate?: boolean;
  ignoreError?: boolean;
}

const cacheTime = 1000 * 60 * 60 * 6; // 6 hours

class ClientNode {
  client: Client;
  #name: string;

  constructor(client: Client, name: string) {
    this.client = client;
    this.#name = name;
  }

  get(type: ClientType, session: string) {
    let name = this.#name;

    switch (type) {
      case ClientType.main:
        name = this.#name;
        break;
      case ClientType.background:
        name = this.#name + '#background';
        break;
      case ClientType.poll:
        name = this.#name + '#poll';
        break;
      default:
        throw new Error(`Invalid client from type ${type}`);
    }

    this.client.name = name;
    this.client.session = session;
    return this.client;
  }

  release() {
    const service = global.app.service.get(ServiceType.Server);
    return service.pool.release(this);
  }

  destroy() {
    const service = global.app.service.get(ServiceType.Server);
    return service.pool.destroy(this);
  }

  async _destroy() {
    await this.client.close();
  }
}

export interface Endpoint {
  host: string;
  port: number;
}

export default class ServerService extends Service {
  endpoint: Endpoint;

  // intentionally not using a private field here
  private _disconnect_listener: () => void;

  #servers = new Map<string, Server>();
  #sessions: Set<string> = global?.app?.hpx_sessions ?? new Set();
  #clients: Set<ClientNode> = global?.app?.hpx_clients ?? new Set();
  #emitter: EventEmitter = new EventEmitter();

  // intentionally not using a private field here
  private _pool: GenericPool.Pool<ClientNode> | undefined;

  constructor(endpoint?: Endpoint) {
    super(ServiceType.Server);

    global.app.hpx_sessions = this.#sessions;
    global.app.hpx_clients = this.#clients;

    log.enabled = false;
    log.logger = {
      debug: global.app.log.d,
      info: global.app.log.i,
      warning: global.app.log.w,
      error: global.app.log.e,
    };

    this.endpoint = endpoint ?? { host: 'localhost', port: 7007 };

    this._pool =
      global?.app?.hpx_pool ??
      GenericPool.createPool(
        {
          create: async () => {
            const node = new ClientNode(
              new Client({ name: CLIENT_NAME }),
              CLIENT_NAME
            );

            this.#clients.add(node);
            return node;
          },
          validate: async (node) => {
            if (!node.client.is_connected()) {
              for (const n of this.#clients) {
                if (n.client.is_connected()) {
                  const [host, port] = n.client.endpoint;
                  await node.client.connect({ host, port });
                  break;
                }
              }
            }
            return true;
          },
          destroy: async (node) => {
            await node._destroy();
            this.#clients.delete(node);
          },
        },
        {
          max: CLIENT_POOL_SIZE,
          min: 1,
          testOnBorrow: true,
          priorityRange: 3,
        }
      );

    if (!global?.app?.hpx_pool) {
      this._pool.on('factoryCreateError', (err) => {
        global.app.log.e('Error occurred in client pool:create', err);
      });

      this._pool.on('factoryDestroyError', (err) => {
        global.app.log.e('Error occurred in client pool:destroy', err);
      });
    }

    global.app.hpx_pool = this._pool;

    this._disconnect_listener = () => {
      this.emit('disconnect', this.endpoint);
    };

    this.on('disconnect', () => this._on_disconnect());
  }

  async init(locator: ServiceLocator) {
    this._pool.start();
  }

  get pool() {
    return this._pool;
  }

  async client(type: ClientType) {
    let priority: PoolPriority = PoolPriority.MEDIUM;

    switch (type) {
      case ClientType.main:
        priority = PoolPriority.MEDIUM;
        break;
      case ClientType.background:
        priority = PoolPriority.LOW;
        break;
      case ClientType.poll:
        priority = PoolPriority.HIGH;
        break;
    }

    const node = await this._pool.acquire(priority);

    return node;
  }

  private _on_disconnect() {
    this.#sessions.clear();
    global.app.hpx_sessions = this.#sessions;
    this.#servers.clear();
    this.#clients.forEach((client) => client.destroy());
    global.app.hpx_clients = this.#clients;
  }

  off(event: string, listener: (...args: any[]) => void): this {
    this.#emitter.off(event, listener);
    return this;
  }

  on(event: 'disconnect', listener: (endpoint: Endpoint) => void): this;
  on(event: 'connect', listener: (endpoint: Endpoint) => void): this;
  on(
    event: 'login',
    listener: (endpoint: Endpoint, session: string) => void
  ): this;
  on(
    event: 'logout',
    listener: (endpoint: Endpoint, session: string) => void
  ): this;
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
    this.#clients.forEach(async (node) => {
      await node._destroy();
      node.client.off('close', this._disconnect_listener);
    });
  }

  async connect(endpoint?: { host: string; port: number }) {
    const node = await this.client(ClientType.main);
    try {
      const client = node.get(ClientType.main, '');
      if (client.is_connected()) {
        if (
          endpoint.host === this.endpoint.host &&
          endpoint.port == this.endpoint.port
        ) {
          global.app.log.i(
            'Already connected to HPX server at ' +
            this.endpoint.host +
            ':' +
            this.endpoint.port
          );
          return;
        } else {
          global.app.log.i(
            'New HPX server endpoint specificed while old connection exists, closing old connection'
          );
          this._close_clients();
        }
      }

      const n_endpoint = endpoint ?? this.endpoint;

      global.app.log.i(
        'Connecting to HPX server... at ' +
        n_endpoint.host +
        ':' +
        n_endpoint.port
      );

      if (!client.is_connected()) {
        for (const n of this.#clients) {
          await n.client.connect(n_endpoint);
        }

        client.on('close', this._disconnect_listener);

        this.emit('connect', n_endpoint);
        this.endpoint = n_endpoint;
      }
    } finally {
      await node.release();
    }
  }

  async login(user?: string, password?: string) {
    const node = await this.client(ClientType.main);

    try {
      global.app.log.d(
        'Logging in to HPX server... at ' +
        this.endpoint.host +
        ':' +
        this.endpoint.port
      );

      const client = node.get(ClientType.main, '');

      const s = await client.handshake({ user, password });
      if (s) {
        const session = client.session;
        this._create_server(session);
        // link the others
        for (const n of this.#clients) {
          if (n.client != client) {
            n.client.session = session;
          }
        }

        this.emit('login', this.endpoint, session);
        return session;
      }
      return null;
    } finally {
      await node.release();
    }
  }

  async logout(session: string) {
    const server = this.#servers.get(session);
    if (server) {
      const node = await this.client(ClientType.main);

      try {
        global.app.log.d(
          'Logging out of HPX server... at ' +
          this.endpoint.host +
          ':' +
          this.endpoint.port
        );

        const client = node.get(ClientType.main, session);

        await client.drop_auth();
        server.accepted = false;
        this.#servers.delete(session);
        this.#sessions.delete(session);

        this.emit('logout', this.endpoint, session);
        global.app.log.d(
          'Successfully logged out of HPX server at ' +
          this.endpoint.host +
          ':' +
          this.endpoint.port,
          ' (',
          session,
          ')'
        );
        return true;
      } finally {
        await node.release();
      }
    }
    global.app.log.d(
      'Failed to log out of HPX server at ' +
      this.endpoint.host +
      ':' +
      this.endpoint.port,
      ' because of invalid session (',
      session,
      ')'
    );
    return false;
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

  is_connected() {
    const [node] = this.#clients;
    if (node) {
      return node.client.is_connected();
    }
    return false;
  }

  session(session: string) {
    // This adds HMR support
    if (
      process.env.NODE_ENV === 'development' &&
      this.#sessions.has(session) &&
      !this.#servers.has(session)
    ) {
      this._create_server(session);
      this.emit('login', this.endpoint, session);
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
  public query_client: QueryClient;

  accepted = false;

  constructor(session: string) {
    this.session = session;

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
    const client_type = options?.client ?? ClientType.main;
    if (group) {
      return await group._group_call(this, client_type, func, args, options);
    }

    const r = await queryClientFetchQuery(
      this,
      client_type,
      [[func, args]],
      options
    );

    const data = r?.data?.[0];

    throw_msg_error(data, options);

    // global.app.log.d('HPX call', func, args, '->', data)

    return data;
  }

  get logged_in() {
    return this.accepted;
  }

  create_group_call() {
    return new GroupCall();
  }

  async properties<
    K extends {
      token: string;
      version: {
        core: [number, number, number];
        db: [number, number, number];
        torrent: [number, number, number];
        beta: boolean;
        alpha: boolean;
        name: string;
        build: string;
      };
      user: ServerUser;
      state: ApplicationState;
      update: [number, number, number];
      guest_allowed: boolean;
      no_namespace_key: string;
      webserver: {
        host: string;
        port: number;
        ssl: boolean;
      };
      pixie: {
        connect: string;
      };
    },
    P extends DeepPickPathPlain<K>
  >(
    args: {
      keys: P[];
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_properties', args, group, options);
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

  async new_item<R = undefined>(
    args: {
      item_type: ItemType;
      item: Record<string, AnyJson>;
      options?: JsonMap;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('new_item', args, group, {
      invalidate: true,
      ...options,
    });

    return data.data as boolean;
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

  async count(
    args: {
      item_type: ItemType;
      metatags?: Partial<Omit<ServerMetaTags, keyof ServerItem>>;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_count', args, group, {
      ...options,
    });

    return data.data as { count: number };
  }

  async related_count(
    args: {
      item_type: ItemType;
      item_id: number
      related_type: ItemType;
      metatags?: Partial<Omit<ServerMetaTags, keyof ServerItem>>;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_related_count', args, group, {
      ...options,
    });

    return data.data as { id: number, count: number };
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
    args: { command_ids: string[]; raise_error?: boolean },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('get_command_value', args, group, options);

    return data.data as Record<CommandIDKey, R>;
  }

  async command_progress(
    args: { command_ids: CommandID<any>[] },
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

  async reindex(
    args: {
      limit?: number;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('reindex', args, group, {
      ...options,
    });

    return data.data as CommandID<{
      status: boolean;
    }>;
  }

  async scan_galleries(
    args: {
      path: string;
      patterns?: string[];
      options?: JsonMap;
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

    return data.data as CommandID<{
      command_id: string;
      view_id: string;
    }>;
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

    return data.data as TransientView<T>;
  }

  async transient_view_action(
    args: {
      view_id: ViewID;
      action: TransientViewAction;
      value?: AnyJson;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('transient_view_action', args, group, {
      ...options,
    });

    return data.data as CommandID<boolean>;
  }

  async transient_view_submit(
    args: {
      view_id: ViewID;
      action: TransientViewSubmitAction;
      value?: AnyJson;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('transient_view_submit', args, group, {
      ...options,
    });

    return data.data as CommandID<boolean>;
  }

  async create_transient_view(
    args: {
      type: TransientViewType;
      view_id?: ViewID;
      options?: JsonMap;
      properties?: JsonMap;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('create_transient_view', args, group, {
      ...options,
    });

    return data.data as ViewID;
  }

  async update_transient_view(
    args: {
      view_id: ViewID;
      options?: JsonMap;
      properties?: JsonMap;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('update_transient_view', args, group, {
      ...options,
    });

    return data.data as boolean;
  }

  async transient_views<T extends TransientViewType>(
    args: {
      view_type?: T;
    },
    group?: GroupCall,
    options?: CallOptions
  ) {
    const data = await this._call('transient_views', args, group, {
      ...options,
    });

    return data.data as TransientView<T>[];
  }
}

async function clientCall(ctx: QueryFunctionContext) {
  const server = ctx.meta.server as Server;
  const type = ctx.meta.type as ClientType;
  const calls = ctx.meta.calls as [fname: string, args: JsonMap][];
  const fnames = calls.map((v) => v[0]);

  global.app.log.d('calling', ...calls.flat());
  const node = await global.app.service.get(ServiceType.Server).client(type);
  try {
    const client = node.get(type, server.session);

    const d = await client.send(
      'call',
      calls.map((c) => ({
        fname: c[0],
        ...c[1],
      }))
    );

    global.app.log.d(fnames, 'received data');
    throw_msg_error(d);

    return d;
  } catch (e) {
    if (
      e instanceof ServerDisconnectError ||
      e.message.includes('not connected')
    ) {
      const fairy = global.app.service.get(ServiceType.Fairy);
      fairy.healthcheck();
    }

    if (
      e instanceof AuthError ||
      [
        exception_codes.AuthError,
        exception_codes.AuthMissingCredentials,
        exception_codes.AuthRequiredError,
        exception_codes.AuthWrongCredentialsError,
      ].includes(e?.code)
    ) {
      server.accepted = false;
    }

    throw e;
  } finally {
    await node.release();
  }
}

async function queryClientFetchQuery(
  server: Server,
  client_type: ClientType,
  calls: [fname: string, args: JsonMap][],
  call_options?: CallOptions
) {
  if (call_options?.invalidate) {
    const fnames = calls.map((v) => v[0]);
    global.log.d('invalidating cache by', ...fnames);
    await server.query_client.invalidateQueries();
  }

  const key = calls.flat();
  return server.query_client.fetchQuery(key, clientCall, {
    cacheTime: !call_options?.cache ? 0 : cacheTime,
    meta: {
      server,
      type: client_type,
      calls,
    },
  });
}

function throw_msg_error(
  msg: ServerMsg<any> | ServerFunctionMsg,
  options?: CallOptions
) {
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
  #client_type: ClientType;
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
    client_type: ClientType,
    func: string,
    args: JsonMap,
    options?: CallOptions
  ) {
    if (this.#resolved) {
      throw Error('Group call already resolved');
    }

    if (
      this.server &&
      this.server !== server &&
      this.server.session !== server.session
    ) {
      throw Error(
        'Trying to assign a server belonging to a different client to a group call; This is likely a bug'
      );
    }

    this.server = server;
    this.#client_type = client_type;
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
        this.server,
        this.#client_type,
        this.#functions.map((f) => [f.name, f.args]),
        this.#options
      );

      throw_msg_error(data);
      data?.data?.forEach?.((r, idx) => {
        try {
          throw_msg_error(r);
          this.#promises_resolves[idx][0](r);
        } catch (err) {
          this.#promises_resolves[idx][1](err);
          if (opt?.throw_error !== false) {
            throw new CancelledError(
              `Group call cancelled due to error in one of the calls: ${err?.message}`
            );
          }
        }
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

  async throw_errors() {
    if (!this.#resolved) {
      throw Error('Group call not resolved. Call "GroupCall.call()" first');
    }
    const r = await Promise.allSettled(this.#promises);
    r.forEach((v) => {
      if (
        v.status === 'rejected' &&
        v.reason !== timeoutError &&
        v.reason !== CancelledError
      ) {
        throw v.reason;
      }
    });
  }
}
