import { ClientError } from '../misc/error';
import { ServiceType } from './constants';

import type PixieService from './pixie';
import type ServerService from './server';
export class Service {
  type: ServiceType;

  constructor(type: ServiceType) {
    this.type = type;
  }
}

type ServiceTypeMap = {
  [ServiceType.Server]: ServerService;
  [ServiceType.Pixie]: PixieService;
};

export class ServiceLocator {
  #instances: { [key in ServiceType]?: Service } = {};

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
