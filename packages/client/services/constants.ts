export enum ServiceType {
  Server,
}

export const STATIC_FOLDER = process.env.HPX_STATIC_FOLDER
  ? process.env.HPX_STATIC_FOLDER
  : '.';
