import PQueue from 'p-queue';
import { Request } from 'zeromq';

import { Decoder, Encoder } from '@msgpack/msgpack';

import { PIXIE_ENDPOINT, ServiceType } from '../server/constants';
import { Service } from './base';

import type { Endpoint } from './server';

export async function getPixie() {
  const pixie = global.app.service.get(ServiceType.Pixie);
  if (!pixie.connected) {
    throw new Error('Pixie is not connected');
  }
  return pixie;
}

export interface PluginInfo {
  id: string;
  name: string;
  shortname: string;
  author: string;
  website: string;
  description: string;
  version: string;
  site: string;
}

type T = {
  version: any;
  user: any;
  state: any;
  update: any;
  guest_allowed: any;
  no_namespace_key: any;
  webserver: {
    host: any;
    port: any;
    ssl: any;
  };
  pixie: {
    connect: any;
  };
};

export default class PixieService extends Service {
  #endpoint: string;
  #server_endpoint: Endpoint;

  #queue: PQueue;
  #decoder: Decoder;
  #encoder: Encoder;
  #socket: Request;
  #connected: boolean;

  #session: string = '';

  constructor(endpoint?: string) {
    super(ServiceType.Pixie);
    this.#connected = false;
    this.#queue = new PQueue({ concurrency: 1 });
    this.#endpoint = endpoint;
    this.#encoder = new Encoder();
    this.#decoder = new Decoder();
    this.#socket = new Request();
    this.#socket.sendHighWaterMark = 1000;
    this.#socket.connectTimeout = 1000 * 5; // 5 sec
    this.#socket.sendTimeout = 1000 * 5; // 5 sec
    this.#socket.receiveTimeout = 1000 * 30; // 30 secs
  }

  async init(locator: ServiceLocator) {
    const server = locator.get(ServiceType.Server);
    server.on('connect', (...args) => this._on_connect(...args));
    server.on('disconnect', (...args) => this._on_disconnect(...args));
    server.on('login', (...args) => this._on_login(...args));
  }

  private _on_connect(endpoint: Endpoint) {
    if (PIXIE_ENDPOINT) {
      this.#server_endpoint = endpoint;

      if (!this.#connected) {
        global.app.log.d(
          'Pixie connecting after server connect (',
          endpoint,
          ')'
        );

        this.connect(PIXIE_ENDPOINT);
      }
    }
  }

  private _on_disconnect(endpoint: Endpoint) {
    if (this.#connected) {
      this.#socket.disconnect(this.#endpoint);
    }
    this.#connected = false;
  }

  private _on_login(endpoint: Endpoint, session: string) {
    if (
      !this.#connected ||
      !(
        endpoint.host === this.#server_endpoint.host &&
        endpoint.port === this.#server_endpoint.port
      )
    ) {
      const server = global.app.service
        .get(ServiceType.Server)
        .session(session);

      this.#connected = false;
      this.#session = session;
      this.#server_endpoint = endpoint;

      global.app.log.d(
        'Pixie connecting after login (',
        session,
        ', ',
        endpoint,
        ')'
      );

      server
        .properties({
          keys: ['pixie.connect'],
        })
        .then((props) => {
          global.app.log.d('Pixie props', props);
          this.connect(props.pixie.connect);
        });
    }
  }

  get connected() {
    return this.#connected;
  }

  get isLocal() {
    return (
      this.#endpoint.includes('localhost') ||
      this.#endpoint.includes('127.0.0.1')
    );
  }

  private async connect(endpoint?: string) {
    if (!this.connected) {
      const e = endpoint ?? this.#endpoint;
      global.app.log.i('Connecting pixie to', e);
      this.#socket.connect(e);
      this.#endpoint = e;
      global.app.log.i('Successfully connected pixie to', e);
      this.#connected = true;
    }
  }

  async plugin({ plugin_id }: { plugin_id: string }) {
    const r = await this.communicate({
      name: 'plugin_info',
      id: plugin_id,
    });
    return r?.data as {
      info: PluginInfo;
      default_site: string;
      version: string;
      version_web: string;
      version_db: string;
    };
  }

  async image({
    l1 = undefined,
    l2 = undefined,
    l3 = undefined,
    p1 = undefined,
    p2 = undefined,
    p3 = undefined,
    i = undefined,
    it = undefined,
    s = undefined,
    cid = undefined,
    t = undefined,
  }) {
    let r: {
      data: Buffer | null;
    };
    if (i && it && s) {
      r = await this.communicate({
        name: 'image_generate',
        id: i,
        item_type: it,
        size: s,
        command_id: cid ?? null,
      });
    } else if (l1 && l2 && l3) {
      r = await this.communicate({
        name: 'image_link',
        link: [l1, l2, l3],
        type: t,
      });
    } else if (p1 && p2 && p3) {
      r = await this.communicate({
        name: 'image_path',
        link: [p1, p2, p3],
        type: t,
      });
    }
    return r;
  }

  async communicate(msg: unknown) {
    if (!this.connected) {
      throw Error('Pixie not connected');
    }

    global.app.log.d('Sending pixie message', msg);
    await this.#queue.add(async () => {
      await this.#socket.send(this.#encoder.encode(msg));
      global.app.log.d('Sent pixie message', msg);
    });
    const [r] = await this.#socket.receive();
    const d: any = this.#decoder.decode(r);
    if (d?.error) {
      const e = Error(d.error);
      e.code = d?.code;
      throw e;
    }
    return d;
  }
}
