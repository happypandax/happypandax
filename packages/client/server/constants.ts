export enum ServiceType {
  Server,
  Pixie,
  Fairy,
}


export const IS_SERVER = typeof window === 'undefined';

export const THUMB_STATIC_FOLDER = process.env.HPX_THUMB_STATIC_FOLDER
  ? process.env.HPX_THUMB_STATIC_FOLDER
  : '.';

export const ITEM_THUMB_STATIC_FOLDER = process.env.HPX_ITEM_THUMB_STATIC_FOLDER
  ? process.env.HPX_ITEM_THUMB_STATIC_FOLDER
  : '.';

export const PAGE_STATIC_FOLDER = process.env.HPX_PAGE_STATIC_FOLDER
  ? process.env.HPX_PAGE_STATIC_FOLDER
  : '.';

export const PIXIE_ENDPOINT = process.env.HPX_PIXIE_ENDPOINT
  ? process.env.HPX_PIXIE_ENDPOINT
  : '';

export const HPX_SERVER_HOST = process.env.HPX_SERVER_HOST
  ? process.env.HPX_SERVER_HOST
  : 'localhost';

export const HPX_SECRET = process.env.HPX_SECRET
  ? process.env.HPX_SECRET
  : 'secret';

export const HPX_SERVER_PORT = process.env.HPX_SERVER_PORT
  ? parseInt(process.env.HPX_SERVER_PORT, 10)
  : 7007;

export const DOMAIN_URL = process.env.PUBLIC_DOMAIN_URL ? process.env.PUBLIC_DOMAIN_URL : 'http://localhost:7008';

export enum LOGIN_ERROR {
  InvalidCredentials = 'InvalidCredentials',
  ServerNotConnected = 'ServerNotConnected',
}