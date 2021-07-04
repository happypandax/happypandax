import Client from 'happypandax-client';

import { createCache } from '../misc/cache';
import { Service } from './base';
import { ServiceType } from './constants';

export default class ServerService extends Service {
  cache: ReturnType<typeof createCache>;

  #client: Client;

  constructor() {
    super(ServiceType.Server);
    this.#client = new Client({ name: 'next-client' });
    this.cache = createCache();
  }

  async _call(func: string, ...args) {
    return this.#client.send([]);
  }

  get logged_in() {
    return this.#client._accepted;
  }

  async login(user?: string, password?: string) {
    const r = await this.#client
      .request_auth()
      .then((m) => this.#client.handshake({ user, password }));
    return r;
  }

  async library() {}
}
