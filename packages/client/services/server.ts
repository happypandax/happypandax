import Client, { JsonMap, ServerErrorMsg, ServerMsg } from 'happypandax-client';

import { createCache } from '../misc/cache';
import { ItemSort, ItemType, ViewType } from '../misc/enums';
import { Service } from './base';
import { ServiceType } from './constants';

export default class ServerService extends Service {
  cache: ReturnType<typeof createCache>;
  endpoint: { host: string; port: number };

  #client: Client;

  constructor(endpoint?: { host: string; port: number }) {
    super(ServiceType.Server);

    this.#client = new Client({ name: 'next-client' });
    this.cache = createCache();
    this.endpoint = endpoint ?? { host: 'localhost', port: 7007 };
  }

  _throw_msg_error(msg: ServerMsg) {
    if (msg.error) {
      const msgerror: ServerErrorMsg = msg.error;
      const err = Error(`${msgerror.code}: ${msgerror.msg}`);
      err.data = msg;
      throw err;
    }
  }

  async _call(func: string, args: JsonMap) {
    const data = await this.#client
      .send([
        {
          fname: func,
          ...args,
        },
      ])
      .then((d) => {
        this._throw_msg_error(d);
        return d?.data?.[0];
      });

    return data;
  }

  get logged_in() {
    return this.#client._accepted;
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

  async library(args: {
    item_type: ItemType;
    filter_id?: number;
    view_filter?: ViewType;
    page?: number;
    limit?: number;
    sort_by?: ItemSort;
    sort_desc?: boolean;
    search_query?: string;
    search_options?: {};
  }) {
    const data = await this._call('library_view', args);
    this._throw_msg_error(data);
    return data.data;
  }
}
