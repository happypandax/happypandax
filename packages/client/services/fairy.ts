import { Channel, Session } from 'better-sse';
import { NextApiRequest } from 'next';

import { ServiceType } from '../server/constants';
import { NotificationData } from '../shared/types';
import { Service } from './base';

export default class FairyService extends Service {
  channel: Channel;
  store: Record<string, NotificationData[]>;
  global: NotificationData[];
  constructor() {
    super(ServiceType.Fairy);
    this.global = [];
    this.store = {};
    this.channel = new Channel();
    setTimeout(() => this._healthcheck(), 1000 * 10);
  }

  _healthcheck() {
    this.healthcheck();

    setTimeout(() => this._healthcheck(), 1000 * 30);
  }

  healthcheck() {
    const server = global.app.service.get(ServiceType.Server);
    this.channel.broadcast('status', { connected: server.is_connected() });
  }

  register(req: NextApiRequest, session: Session, id: string) {
    this.channel.register(session);
    this.store[id] = [];
  }

  notify(data: NotificationData, id?: string) {
    if (!data.date) {
      data.date = new Date();
    }

    if (id && this.store?.[id]) {
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
    return d.sort((a, b) => a.date.getTime() - b.date.getTime()).slice(0, 10);
  }
}
