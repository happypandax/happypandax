import { Channel, Session } from 'better-sse';
import { NextApiRequest } from 'next';

import { NotificationData } from '../misc/types';
import { Service } from './base';
import { ServiceType } from './constants';

export default class FairyService extends Service {
  channel: Channel;
  store: Record<string, NotificationData[]>;
  global: NotificationData[];
  constructor() {
    super(ServiceType.Fairy);
    this.global = [];
    this.store = {};
    this.channel = new Channel();
    setTimeout(() => this.status(), 1000 * 10);
  }

  status() {
    const server = global.app.service.get(ServiceType.Server);

    this.channel.broadcast('status', server.status());

    setTimeout(() => this.status(), 1000 * 30);
  }

  register(req: NextApiRequest, session: Session, id: string) {
    this.channel.register(session);
    this.store[id] = [];
  }

  notify(data: NotificationData, id?: string) {
    if (!data.date) {
      data.date = new Date();
    }

    if (id && this.store[id]) {
      const l = this.store[id].unshift(data);
      if (l > 10) {
        this.store[id].pop();
      }
    } else if (!id) {
      const l = this.global.unshift(data);
      if (l > 10) {
        this.global.pop();
      }
    }

    global.app.log.d('notifying client with', data);

    this.channel.broadcast('notification', data);
  }

  get(id: string) {
    const d = [...this.global, ...(this.store?.[id] ?? [])];
    return d.sort((a, b) => a.date.getTime() - b.date.getTime()).slice(10);
  }
}
