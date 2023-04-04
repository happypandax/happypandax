import { ServiceType } from '../server/constants';
import { ClientError } from '../shared/error';

import type FairyService from './fairy';
import type PixieService from './pixie';
import type ServerService from './server';
export class Service {
  type: ServiceType;

  constructor(type: ServiceType) {
    this.type = type;
  }

  async init(locator: ServiceLocator) {}
}

type ServiceTypeMap = {
  [ServiceType.Server]: ServerService;
  [ServiceType.Pixie]: PixieService;
  [ServiceType.Fairy]: FairyService;
};

export class ServiceLocator {
  #instances: { [key in ServiceType]?: Service } = {};

  init(locator: ServiceLocator) {
    return Promise.all(
      Object.values(this.#instances).map((s) => s?.init(locator))
    );
  }

  set<T extends Service>(instance: T) {
    this.#instances[instance.type] = instance;
  }

  get<T extends ServiceType>(type: T) {
    const instance = this.#instances[type];
    if (!instance) {
      throw new ClientError('No service of type', type, 'found');
    }

    return instance as ServiceTypeMap[T];
  }
}
