import EventEmitter from 'events';
import { TimeoutError } from 'happypandax-client';
import { networkInterfaces } from 'os';
import PQueue from 'p-queue';
import { Dealer } from 'zeromq';

import { Decoder, Encoder } from '@msgpack/msgpack';

import {
  HPX_DOMAIN_URL,
  HPX_INSTANCE_TOKEN,
  HPX_SERVER_HOST,
  HPX_SERVER_PORT,
  PIXIE_ENDPOINT,
  ServiceType,
} from '../server/constants';
import { Service } from './base';

import type { Endpoint } from './server';
export async function getPixie(connected = true) {
  const pixie = global.app.service.get(ServiceType.Pixie);
  if (connected && !pixie.connected) {
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

  TIMEOUT = 1000 * 30 // 30 sec

  #endpoint: string;
  #server_endpoint: Endpoint = {
    host: HPX_SERVER_HOST,
    port: HPX_SERVER_PORT
  };
  #webserver_endpoint: string = HPX_DOMAIN_URL;
  #instance_token: string = HPX_INSTANCE_TOKEN;

  #emitter: EventEmitter;

  #recv_queue: PQueue;

  #queues: PQueue[];
  #sockets: Dealer[];

  #decoder: Decoder;
  #encoder: Encoder;
  #connected: boolean;

  #session: string = '';

  constructor(endpoint?: string, connections = 2) {
    super(ServiceType.Pixie);
    this.#connected = false;
    this.#endpoint = endpoint;

    this.#emitter = new EventEmitter();

    this.#encoder = new Encoder();
    this.#decoder = new Decoder();

    this.#recv_queue = new PQueue({ concurrency: connections });

    this.#queues = [];
    this.#sockets = [];

    for (let i = 0; i < connections; i++) {

      this.#queues.push(new PQueue({ concurrency: 1 }))

      const s = new Dealer();
      s.sendHighWaterMark = 1000;
      s.connectTimeout = 1000 * 5; // 5 sec
      s.sendTimeout = 1000 * 5; // 5 sec
      s.receiveTimeout = -1; // forever

      this.#sockets.push(s);

    }

    this.#sockets.forEach((s) => {
      this.#recv_queue.add(() => this._recv(s));
    });
  }

  async init(locator: ServiceLocator) {
    const server = locator.get(ServiceType.Server);
    server.on('connect', (...args) => this._on_connect(...args));
    server.on('disconnect', (...args) => this._on_disconnect(...args));
    server.on('login', (...args) => this._on_login(...args));

    if (HPX_INSTANCE_TOKEN && PIXIE_ENDPOINT) {
      this.connect(PIXIE_ENDPOINT);
    }
  }

  get webserver_endpoint() {
    if (!this.#webserver_endpoint) {
      return '';
    }

    return this.#webserver_endpoint
  }

  get connected() {
    return this.#connected;
  }

  _isLocal(endpoint: Endpoint) {
    const nets = networkInterfaces();
    const ips = Object.values(nets).flat().map(net => net.address);

    return (
      endpoint?.host === 'localhost' ||
      ips.includes(endpoint?.host)
    )
  }

  get isLocal() {
    return this._isLocal(this.#server_endpoint);
  }

  get isHPXInstanced() {
    return (
      this.isLocal && !!HPX_INSTANCE_TOKEN
    );
  }

  get HPXToken() {
    return this.#instance_token ?? '';
  }

  private async _recv(socket: Dealer) {
    const [r] = await socket.receive();
    const d: any = this.#decoder.decode(r);
    this.#emitter.emit("data", d);
    this.#recv_queue.add(() => this._recv(socket));
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
      this.#sockets.forEach((s) => s.disconnect(this.#endpoint));
    }
    this.#connected = false;
  }

  private _on_login(endpoint: Endpoint, session: string) {

    if (!this.#webserver_endpoint || !this.#instance_token) {
      const server = global.app.service
        .get(ServiceType.Server)
        .session(session);

      server
        .properties({
          keys: ['webserver', 'token'],
        })
        .then((props) => {

          this.#webserver_endpoint = (props.webserver.ssl ? 'https://' : 'http://')
            + props.webserver.host + ':'
            + props.webserver.port
          this.#instance_token = props.token;
        });
    }

    if (
      !this.#connected ||
      !(
        endpoint?.host === this.#server_endpoint?.host &&
        endpoint?.port === this.#server_endpoint?.port
      )
    ) {
      const server = global.app.service
        .get(ServiceType.Server)
        .session(session);

      this.#connected = false;
      this.#session = session;
      this.#server_endpoint = endpoint;

      if (this._isLocal(endpoint)) {
        global.app.log.d(
          'Pixie connecting after login (',
          endpoint,
          ')'
        );

        server
          .properties({
            keys: ['pixie.connect'],
          })
          .then((props) => {
            this.connect(props.pixie.connect);
          });
      } else {
        global.app.log.w(
          'Client is not local, will not connect pixie'
        );

      }

    }
  }


  private async connect(endpoint?: string) {
    if (!this.connected) {
      const e = endpoint ?? this.#endpoint;
      global.app.log.i('Connecting pixie to', e);
      this.#sockets.forEach((s) => s.connect(e));
      this.#endpoint = e;
      global.app.log.i('Successfully connected pixie to', e);
      this.#connected = true;

      // TODO: 
      // this.properties().then((props) => {});
    }
  }

  private _generate_msg_id() {
    return Math.floor(Math.random() * 10000000000);
  }

  async properties() {
    const r = await this.communicate({
      msgid: this._generate_msg_id(),
      name: 'properties',
    });
    return r?.data as {
    };
  }

  async plugin({ plugin_id }: { plugin_id: string }) {
    const r = await this.communicate({
      msgid: this._generate_msg_id(),
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
        msgid: this._generate_msg_id(),
        name: 'image_generate',
        id: i,
        item_type: it,
        size: s,
        command_id: cid ?? null,
      });
    } else if (l1 && l2 && l3) {
      r = await this.communicate({
        msgid: this._generate_msg_id(),
        name: 'image_link',
        link: [l1, l2, l3],
        type: t,
      });
    } else if (p1 && p2 && p3) {
      r = await this.communicate({
        msgid: this._generate_msg_id(),
        name: 'image_path',
        link: [p1, p2, p3],
        type: t,
      });
    }
    return r;
  }

  communicate(message: { msgid: any } & Record<string, any>) {

    return new Promise((resolve, reject) => {

      if (!this.connected) {
        throw Error('Pixie not connected');
      }

      const msg = { ...message, token: this.HPXToken };

      // global.app.log.d('Sending pixie message', msg);

      let idx = 0;
      let size = 0

      this.#queues.forEach((q, i) => {
        if (size === 0) {
          size = q.size;
          idx = i;
        } else if (q.size < size) {
          size = q.size;
          idx = i;
        }
      });

      const queue = this.#queues[idx];
      const socket = this.#sockets[idx];

      const cb = (data: {
        msgid?: any,
        error?: any,
      }) => {
        let e: any = undefined
        if (data.msgid === msg.msgid) {
          if (data?.error) {
            e = Error(data.error);
            e.code = data?.code;
          } else {
            this.#emitter.off("data", cb);
            resolve(data);
          }
        } else if (!data.msgid) {
          e = Error(data.error);
          e.code = data?.code;
        }

        if (e) {
          this.#emitter.off("data", cb);
          reject(e);
        }
      }

      this.#emitter.on("data", cb);

      queue.add(async () => {
        await socket.send(this.#encoder.encode(msg));
      });

      setTimeout(() => {
        const e = new TimeoutError("Did not receive pixie response in time")
        reject(e)
      }, this.TIMEOUT)
    })
  }
}
