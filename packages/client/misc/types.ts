export type ItemSize = 'tiny' | 'mini' | 'small' | 'medium' | 'large';

export interface DragItemData {
  data: { id: number };
}

export interface ServerItem {
  id: number;
  timestamp: number;
}

export interface ServerParody extends ServerItem {}
export interface ServerCircle extends ServerItem {
  name: string;
  user_id: number;
}
export interface ServerUrl extends ServerItem {}
export interface ServerLanguage extends ServerItem {
  name: string;
  code: string;
  user_id: number;
}

export interface ServerItemName extends ServerItem {
  language: ServerLanguage;
  language_id: number;
  alias_for_id: number;
  name: string;
}

export interface ServerMetaTags extends ServerItem {
  favorite: boolean;
  inbox: boolean;
  readlater: boolean;
  trash: boolean;
  follow: boolean;
  read: boolean;
  name: boolean;
  session: boolean;
}
export interface ServerArtist extends ServerItem {
  names: (ServerItemName & { artist_id: number })[];
  preferred_name: ServerItemName & { artist_id: number };
  circles: ServerCircle[];
  info: string;
  user_id: number;
  metatags: ServerMetaTags;
  urls: ServerUrl[];
}

export interface ServerGalleryTitle extends ServerItem {
  language: ServerLanguage;
  name: string;
  language_id: number;
  gallery_id: number;
  alias_for_id: number;
  user_ud: number;
}

type ServerItemTrash = {};

export interface ServerGallery {
  id: number;
  titles: ServerGalleryTitle[];
  artists: ServerArtist[];
  circles: ServerCircle[];
  parodies: ServerParody[];
  last_updated: number;
  last_read: number;
  pub_date: number;
  info: string;
  single_source: boolean;
  phantom: boolean;
  number: number;
  category_id: number;
  language_id: number;
  grouping_id: number;
  taggable_id: number;
  user_id: number;
  metatags: ServerMetaTags;
  urls: ServerUrl[];
  preferred_title: ServerGalleryTitle;
  times_read: number;
  rating: number;
  trash: ServerItemTrash;
}
