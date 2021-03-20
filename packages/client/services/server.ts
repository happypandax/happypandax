import { Service } from './base';
import { ServiceType } from './constants';

export default class ServerService extends Service {
  constructor() {
    super(ServiceType.Server);
  }
}
