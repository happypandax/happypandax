import { AnyJson } from 'happypandax-client';

import {
  CommandState,
  ImageSize,
  ItemSort,
  ItemType,
  PluginState,
  Priority,
  ProgressType,
} from './enums';

export type ItemSize = 'tiny' | 'mini' | 'small' | 'medium' | 'large';

export interface DragItemData {
  data: { id: number };
}

export interface ServerItem {
  id: number;
  timestamp: number;
  plugin: object;
}

export interface ServerItemWithName extends ServerItem {
  name: string;
}

export interface ServerItemWithUrls extends ServerItem {
  urls: ServerUrl[];
}

export interface ServerItemTaggable extends ServerItem {
  taggable_id: number;
  tags: ServerNamespaceTag[];
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

export interface ServerItemWithMetatags extends ServerItem {
  metatags: ServerMetaTags;
}

export interface ServerParody extends ServerItem, ServerItemWithProfile {
  names: (ServerItemWithNameLanguageAlias & { parody_id: number })[];
  preferred_name: ServerItemWithNameLanguageAlias & { parody_id: number };
}

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

export interface ServerNamespace extends ServerItemWithName {}

export interface ServerTag extends ServerItemWithName {}

export interface ServerNamespaceTag extends ServerItemWithMetatags {
  namespace: ServerNamespace;
  tag: ServerTag;
}

export interface ServerMetaTags extends ServerItem {
  favorite: boolean;
  inbox: boolean;
  trash: boolean;
  follow: boolean;
  read: boolean;
}

export interface ServerArtist
  extends ServerItemWithMetatags,
    ServerItemWithProfile {
  names: (ServerItemWithNameLanguageAlias & { artist_id: number })[];
  preferred_name: ServerItemWithNameLanguageAlias & { artist_id: number };
  circles: ServerCircle[];
  info: string;
  user_id: number;
  urls: ServerUrl[];
}

export interface ServerGrouping
  extends ServerItemWithProfile,
    ServerItemWithName {
  language: ServerLanguage;
  language_id: number;
  status_id: number;
  info: string;
  status: ServerStatus;
  user_id: number;
  gallery_count: number;
  galleries: any;
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
export interface ServerGallery
  extends ServerItem,
    ServerItemWithProfile,
    ServerItemWithUrls,
    ServerItemWithMetatags,
    ServerItemTaggable {
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
  user_id: number;
  progress: ServerGalleryProgress;
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

export interface ServerPage
  extends ServerItemWithMetatags,
    ServerItemWithProfile {
  number: number;
  name: string;
  path: string;
  hash_id: number;
  gallery_id: number;
  in_archive: boolean;
  user_id: number;
}

export interface ServerCollection
  extends ServerItemWithProfile,
    ServerItemWithUrls,
    ServerItemWithMetatags,
    ServerItemWithName {
  info: string;
  pub_date: number;
  category_id: number;
  gallery_count: number;
  last_updated: number;
  category: ServerCategory;
  user_id: number;
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

export type SearchItem = {
  id: number;
  __type__: ItemType;
  [key: string]: AnyJson;
};

export type CommandIDKey = string;

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

export type SortOptions = {
  by?: ItemSort;
  desc?: boolean;
};

export type SearchOptions = {
  regex?: boolean;
  case_sensitive?: boolean;
  match_exact?: boolean;
  match_all_terms?: boolean;
  children?: boolean;
};

export interface CommandID<T> extends String {}

interface _ItemHandler {
  identifier: string;
  name: string;
  sites: string;
  description: string;
  priority: Priority;
  disabled: boolean;
}

export type DownloadHandler = _ItemHandler;
export type MetadataHandler = _ItemHandler;
export interface QueueItem {
  item_id: number;
  title: string;
  subtitle: string;
  text: string;
  value: number;
  percent: number;
  active: boolean;
  state: CommandState;
  success: boolean;
}

export interface MetadataItem extends QueueItem {
  item_type: ItemType;
}

export interface DownloadItem extends QueueItem {
  url: string;
  thumbnail_url: string;
}

export interface NotificationData {
  type: 'info' | 'warning' | 'error';
  title: string;
  body?: string;
  date?: Date;
}

export type ReaderData = Optional<
  DeepPick<
    ServerPage,
    | 'id'
    | 'name'
    | 'number'
    | 'metatags.favorite'
    | 'metatags.inbox'
    | 'metatags.trash'
    | 'profile'
    | 'path'
  >,
  'profile'
>;

export type Version = [number, number, number];
export interface PluginData {
  id: number;
  name: string;
  shortname: string;
  version: Version;
  author: string;
  description: string;
  website: string;
  state: PluginState;
  status: string;
  site: string;
  update_version: Version;
}
