export enum ServiceType {
  Server,
  Pixie,
  Fairy,
}

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
