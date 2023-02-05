import PQueue from 'p-queue';
import { Request } from 'zeromq';

import { Decoder, Encoder } from '@msgpack/msgpack';

import { Service } from './base';
import { PIXIE_ENDPOINT, ServiceType } from './constants';

export async function getPixie() {
  const pixie = global.app.service.get(ServiceType.Pixie);
  if (!pixie.connected) {
    let addr = PIXIE_ENDPOINT;
    if (!addr) {
      const server = global.app.service.get(ServiceType.Server);
      const s = server.status();
      if (s.connected && s.loggedIn) {
        const props = await server.properties({ keys: ['pixie.connect'] });
        addr = props.pixie.connect;
      } else {
        throw Error('server not connected');
      }
    }

    await pixie.connect(addr);
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

export default class PixieService extends Service {
  endpoint: string;

  #queue: PQueue;
  #decoder: Decoder;
  #encoder: Encoder;
  #socket: Request;
  #connected: boolean;

  #session: string = '';

  constructor(endpoint?: string) {
    super(ServiceType.Pixie);
    this.#queue = new PQueue({ concurrency: 1 });
    this.endpoint = endpoint;
    this.#encoder = new Encoder();
    this.#decoder = new Decoder();
    this.#socket = new Request();
    this.#socket.sendHighWaterMark = 1000;
    this.#socket.connectTimeout = 1000 * 5; // 5 sec
    this.#socket.sendTimeout = 1000 * 5; // 5 sec
    this.#socket.receiveTimeout = 1000 * 30; // 30 secs
  }

  get connected() {

    const server = global.app.service.get(ServiceType.Server);
    if (!server.status().connected) {
      if (this.#connected) {
        this.#socket.disconnect(this.endpoint);
      }
      this.#connected = false;
    }

    if (this.#connected && server.client.session !== this.#session) {
      this.#connected = false;
      this.#socket.disconnect(this.endpoint);
    }

    return this.#connected;
  }

  get isLocal() {
    return this.endpoint.includes('localhost') || this.endpoint.includes('127.0.0.1');
  }

  async connect(endpoint?: string) {
    if (!this.connected) {
      const e = endpoint ?? this.endpoint
      global.app.log.i('Connecting pixie to', e);
      this.#socket.connect(e);
      this.endpoint = e;
      global.app.log.i('Successfully connected pixie to', e);

      const server = global.app.service.get(ServiceType.Server);
      this.#session = server.client.session;
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
    global.app.log.d("Sending pixie message", msg)
    await this.#queue.add(async () => {
      await this.#socket.send(this.#encoder.encode(msg));
      global.app.log.d("Sent pixie message", msg)
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
