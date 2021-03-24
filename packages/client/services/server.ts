import Client from 'happypandax-client';
import { Service } from './base';
import { ServiceType } from './constants';

export default class ServerService extends Service {
  client: Client;
  constructor() {
    super(ServiceType.Server);
    this.client = new Client({ name: 'next-client' });
  }
}
