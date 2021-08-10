import PQueue from 'p-queue';
import { Request } from 'zeromq';

import { Decoder, Encoder } from '@msgpack/msgpack';

import { Service } from './base';
import { ServiceType } from './constants';

export default class PixieService extends Service {
  endpoint: string;

  #queue: PQueue;
  #decoder: Decoder;
  #encoder: Encoder;
  #socket: Request;
  #connected: boolean;

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
    return this.#connected;
  }

  async connect(endpoint?: string) {
    this.#socket.connect(endpoint ?? this.endpoint);
    this.#connected = true;
  }

  async image({
    l1 = undefined,
    l2 = undefined,
    l3 = undefined,
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
      let command_id = parseInt(cid);
      if (isNaN(command_id)) {
        command_id = 0;
      }

      r = await this.communicate({
        name: 'image_generate',
        id: i,
        item_type: it,
        size: s,
        command_id,
      });
    } else if (l1 && l2 && l3) {
      r = await this.communicate({
        name: 'image_link',
        link: l1 + '/' + l2 + '/' + l3,
        type: t,
      });
    }
    return r;
  }

  async communicate(msg: unknown) {
    await this.#queue.add(() => this.#socket.send(this.#encoder.encode(msg)));
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
