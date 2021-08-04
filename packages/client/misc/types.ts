import { CommandState, ImageSize, ItemType, ProgressType } from './enums';

export type ItemSize = 'tiny' | 'mini' | 'small' | 'medium' | 'large';

export interface DragItemData {
  data: { id: number };
}

export interface ServerItem {
  id: number;
  timestamp: number;
  plugin: object;
}

interface ServerItemWithName extends ServerItem {
  name: string;
}

interface ServerItemWithNameLanguageAlias extends ServerItemWithName {
  language: ServerLanguage;
  language_id: number;
  alias_for_id: number;
}

export interface ServerItemWithProfile extends ServerItem {
  profile: {
    data: string;
    size: [number, number];
    command_id: number | null;
  };
}

export interface ServerParody extends ServerItem {}

export interface ServerCircle extends ServerItemWithName {
  user_id: number;
}

export interface ServerCategory extends ServerItemWithName {
  user_id: number;
}

export interface ServerUrl extends ServerItemWithName {}
export interface ServerStatus extends ServerItemWithName {}
export interface ServerLanguage extends ServerItemWithName {
  code: string;
  user_id: number;
}

export interface ServerMetaTags extends ServerItem {
  favorite: boolean;
  inbox: boolean;
  readlater: boolean;
  trash: boolean;
  follow: boolean;
  read: boolean;
}
export interface ServerArtist extends ServerItem {
  names: (ServerItemWithNameLanguageAlias & { artist_id: number })[];
  preferred_name: ServerItemWithNameLanguageAlias & { artist_id: number };
  circles: ServerCircle[];
  info: string;
  user_id: number;
  metatags: ServerMetaTags;
  urls: ServerUrl[];
}

export interface ServerGrouping extends ServerItemWithName {
  language: ServerLanguage;
  language_id: number;
  status_id: number;
  status: ServerStatus;
  user_id: number;
}

export interface ServerGalleryTitle extends ServerItem {
  language: ServerLanguage;
  name: string;
  language_id: number;
  gallery_id: number;
  alias_for_id: number;
  user_id: number;
}

type ServerItemTrash = {};

export interface ServerGalleryProgress extends ServerItem {
  gallery_id: number;
  page: ServerPage;
  page_id: number;
  percent: number;
  end: boolean;
  last_updated: number;
  user_id: number;
}
export interface ServerGallery extends ServerItem, ServerItemWithProfile {
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
  category: ServerCategory;
  language_id: number;
  language: ServerLanguage;
  grouping_id: number;
  grouping: ServerGrouping;
  taggable_id: number;
  user_id: number;
  metatags: ServerMetaTags;
  progress: ServerGalleryProgress;
  urls: ServerUrl[];
  preferred_title: ServerGalleryTitle;
  times_read: number;
  rating: number;
  page_count: number;
  trash: ServerItemTrash;
}

export interface ServerFilter extends ServerItem {
  name: string;
  filter: string;
  info: string;
  enforce: boolean;
  search_options: string[];
  user_id: number;
}

export interface ServerPage extends ServerItemWithProfile {
  number: number;
  name: string;
  path: string;
  hash_id: number;
  gallery_id: number;
  in_archive: boolean;
  user_id: number;
  metatags: ServerMetaTags;
}

export type FieldPath<T = undefined> = T extends undefined
  ?
      | DeepPickPathPlain<ServerCircle>
      | DeepPickPathPlain<ServerFilter>
      | DeepPickPathPlain<ServerParody>
      | DeepPickPathPlain<ServerLanguage>
      | DeepPickPathPlain<ServerGallery>
      | DeepPickPathPlain<ServerPage>
      | DeepPickPathPlain<ServerArtist>
  : DeepPickPathPlain<T>;

export interface ServerSortIndex {
  index: number;
  name: string;
  item_type: ItemType;
}

export type CommandID = string;

export interface CommandProgress {
  title: string;
  value: number;
  subtitle: string;
  subtype: ProgressType;
  max: number;
  perfect: number;
  type: ProgressType;
  text: string;
  timestamp: number;
  state: CommandState;
}

export type ProfileOptions = {
  size?: ImageSize;
  url?: boolean;
  uri?: boolean;
};
