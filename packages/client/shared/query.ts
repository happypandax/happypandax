import type { Server } from '../services/server';
import type { RequestOptions } from '../server/requests';
import { FieldPath, ServerSortIndex } from './types';

export enum QueryType {
  PROPERTIES = '/api/properties',
  PROFILE = '/api/profile',
  PAGES = '/api/pages',
  LIBRARY = '/api/library',
  ITEMS = '/api/items',
  ITEM = '/api/item',
  COUNT = '/api/count',
  RELATED_COUNT = '/api/related_count',
  RELATED_ITEMS = '/api/related_items',
  SEARCH_ITEMS = '/api/search_items',
  SIMILAR = '/api/similar',
  SEARCH_LABELS = '/api/search_labels',
  QUEUE_ITEMS = '/api/queue_items',
  QUEUE_STATE = '/api/queue_state',
  SORT_INDEXES = '/api/sort_indexes',
  DOWNLOAD_INFO = '/api/download_info',
  METADATA_INFO = '/api/metadata_info',
  SERVER_STATUS = '/api/status',
  CONFIG = '/api/config',
  LOG = '/api/log',
  PLUGIN = '/api/plugin',
  PLUGINS = '/api/plugins',
  PLUGIN_UPDATE = '/api/plugin_update',
  COMMAND_STATE = '/api/command_state',
  COMMAND_VALUE = '/api/command_value',
  COMMAND_PROGRESS = '/api/command_progress',
  TRANSIENT_VIEW = '/api/transient_view',
  TRANSIENT_VIEWS = '/api/transient_views',
  ACTIVITIES = '/api/activities',
}

export enum MutatationType {
  LOGIN = '/api/auth/callback/happypandax',
  UPDATE_ITEM = '/api/item',
  NEW_ITEM = '/api/item',
  UPDATE_METATAGS = '/api/metatags',
  UPDATE_CONFIG = '/api/config',
  START_COMMAND = '/api/command',
  STOP_COMMAND = '/api/command',
  STOP_QUEUE = '/api/stop_queue',
  START_QUEUE = '/api/start_queue',
  CLEAR_QUEUE = '/api/clear_queue',
  ADD_ITEM_TO_QUEUE = '/api/add_item_to_queue',
  OPEN_GALLERY = '',
  REMOVE_ITEM_FROM_QUEUE = '/api/remove_item_from_queue',
  ADD_ITEMS_TO_METADATA_QUEUE = '/api/add_items_to_metadata_queue',
  ADD_URLS_TO_DOWNLOAD_QUEUE = '/api/add_urls_to_download_queue',
  PAGE_READ_EVENT = '/api/page_read_event',
  INSTALL_PLUGIN = '/api/plugin',
  DISABLE_PLUGIN = '/api/plugin',
  REMOVE_PLUGIN = '/api/plugin',
  UPDATE_PLUGIN = '/api/plugin',
  UPDATE_FILTERS = '/api/update_filters',
  RESOLVE_PATH_PATTERN = '/api/resolve_path_pattern',
  SCAN_GALLERIES = '/api/scan_galleries',
  TRANSIENT_VIEW_ACTION = '/api/transient_view_action',
  TRANSIENT_VIEW_SUBMIT_ACTION = '/api/transient_view_submit',
  CREATE_TRANSIENT_VIEW = '/api/create_transient_view',
  UPDATE_TRANSIENT_VIEW = '/api/update_transient_view',
  REINDEX = '/api/reindex',
}

// ======================== ACTIONS ====================================

export type ServerParameters = {
  [K in keyof Server]:
  | {
    __options?: RequestOptions;
  }
  | Parameters<
    Server[K] extends (...args: any[]) => any ? Server[K] : never
  >[0];
};

export type ServerReturnType = {
  [K in keyof Server]: Unwrap<
    ReturnType<Server[K] extends (...args: any[]) => any ? Server[K] : never>
  >;
};

interface Action {
  variables?: Record<string, any>;
  dataType?: unknown;
}

// ======================== QUERY ACTIONS ====================================

interface QueryAction<T = undefined> extends Action {
  type: QueryType;
}

interface FetchServerStatus<T = undefined> extends QueryAction<T> {
  type: QueryType.SERVER_STATUS;
  dataType: {
    loggedIn: boolean;
    connected: boolean;
  };
}

interface FetchSortIndexes<T = undefined> extends QueryAction<T> {
  type: QueryType.SORT_INDEXES;
  dataType: ServerSortIndex[];
  variables: ServerParameters['sort_indexes'];
}

interface FetchProperties<T = undefined> extends QueryAction<T> {
  type: QueryType.PROPERTIES;
  dataType: ServerReturnType['properties'];
  variables: ServerParameters['properties'];
}

interface FetchProfile<T = undefined> extends QueryAction<T> {
  type: QueryType.PROFILE;
  dataType: ServerReturnType['profile'];
  variables: ServerParameters['profile'];
}

interface FetchItem<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEM;
  dataType: Record<string, any>;
  variables: Omit<ServerParameters['item'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchCount<T = undefined> extends QueryAction<T> {
  type: QueryType.COUNT;
  dataType: ServerReturnType['count'];
  variables: Omit<ServerParameters['count'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchRelatedCount<T = undefined> extends QueryAction<T> {
  type: QueryType.RELATED_COUNT;
  dataType: ServerReturnType['related_count'];
  variables: Omit<ServerParameters['related_count'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchItems<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEMS;
  dataType: ServerReturnType['items'];
  variables: Omit<ServerParameters['items'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSearchItems<T = undefined> extends QueryAction<T> {
  type: QueryType.ITEMS;
  dataType: ServerReturnType['search_items'];
  variables: Omit<ServerParameters['search_items'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchLibrary<T = undefined> extends QueryAction<T> {
  type: QueryType.LIBRARY;
  dataType: ServerReturnType['library'];
  variables: Omit<ServerParameters['library'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchRelatedItems<T = undefined> extends QueryAction<T> {
  type: QueryType.RELATED_ITEMS;
  dataType: ServerReturnType['related_items'];
  variables: Omit<ServerParameters['related_items'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchPages<T = undefined> extends QueryAction<T> {
  type: QueryType.PAGES;
  dataType: ServerReturnType['pages'];
  variables: Omit<ServerParameters['pages'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSimilar<T = undefined> extends QueryAction<T> {
  type: QueryType.SIMILAR;
  dataType: ServerReturnType['similar'];
  variables: Omit<ServerParameters['similar'], 'fields'> & {
    fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
  };
}

interface FetchSearchLabels<T = undefined> extends QueryAction<T> {
  type: QueryType.SEARCH_LABELS;
  dataType: ServerReturnType['search_labels'];
  variables: ServerParameters['search_labels'];
}

interface FetchQueueItems<T = undefined> extends QueryAction<T> {
  type: QueryType.QUEUE_ITEMS;
  dataType: ServerReturnType['queue_items'];
  variables: ServerParameters['queue_items'];
}
interface FetchQueueState<T = undefined> extends QueryAction<T> {
  type: QueryType.QUEUE_STATE;
  dataType: ServerReturnType['queue_state'];
  variables: ServerParameters['queue_state'];
}

interface FetchLog<T = undefined> extends QueryAction<T> {
  type: QueryType.LOG;
  dataType: ServerReturnType['log'];
  variables: ServerParameters['log'];
}

interface FetchDownloadInfo<T = undefined> extends QueryAction<T> {
  type: QueryType.DOWNLOAD_INFO;
  dataType: ServerReturnType['download_info'];
  variables: ServerParameters['download_info'];
}

interface FetchMetadataInfo<T = undefined> extends QueryAction<T> {
  type: QueryType.METADATA_INFO;
  dataType: ServerReturnType['metadata_info'];
  variables: ServerParameters['metadata_info'];
}

interface FetchConfig<T = undefined> extends QueryAction<T> {
  type: QueryType.CONFIG;
  dataType: ServerReturnType['config'];
  variables: ServerParameters['config'];
}

interface FetchPlugin<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGIN;
  dataType: ServerReturnType['plugin'];
  variables: ServerParameters['plugin'];
}

interface FetchPluginUpdate<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGIN_UPDATE;
  dataType: ServerReturnType['check_plugin_update'];
  variables: ServerParameters['check_plugin_update'];
}

interface FetchPlugins<T = undefined> extends QueryAction<T> {
  type: QueryType.PLUGINS;
  dataType: ServerReturnType['list_plugins'];
  variables: ServerParameters['list_plugins'];
}

interface FetchCommandProgress<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_PROGRESS;
  dataType: ServerReturnType['command_progress'];
  variables: ServerParameters['command_progress'];
}

interface FetchCommandState<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_STATE;
  dataType: ServerReturnType['command_state'];
  variables: ServerParameters['command_state'];
}

interface FetchCommandValue<T = undefined> extends QueryAction<T> {
  type: QueryType.COMMAND_VALUE;
  dataType: ServerReturnType['command_value'];
  variables: ServerParameters['command_value'];
}
interface FetchActivities<T = undefined> extends QueryAction<T> {
  type: QueryType.ACTIVITIES;
  dataType: ServerReturnType['activities'];
  variables: ServerParameters['activities'];
}

interface FetchTransientView<T = undefined> extends QueryAction<T> {
  type: QueryType.TRANSIENT_VIEW;
  dataType: ServerReturnType['transient_view'];
  variables: ServerParameters['transient_view'];
}

interface FetchTransientViews<T = undefined> extends QueryAction<T> {
  type: QueryType.TRANSIENT_VIEWS;
  dataType: ServerReturnType['transient_views'];
  variables: ServerParameters['transient_views'];
}

export type QueryActions<T = undefined> =
  | FetchProperties<T>
  | FetchProfile<T>
  | FetchItem<T>
  | FetchCount<T>
  | FetchRelatedCount<T>
  | FetchItems<T>
  | FetchLibrary<T>
  | FetchPages<T>
  | FetchSearchLabels<T>
  | FetchRelatedItems<T>
  | FetchSortIndexes<T>
  | FetchSimilar<T>
  | FetchSearchItems<T>
  | FetchQueueItems<T>
  | FetchQueueState<T>
  | FetchLog<T>
  | FetchDownloadInfo<T>
  | FetchMetadataInfo<T>
  | FetchConfig<T>
  | FetchPlugin<T>
  | FetchPluginUpdate<T>
  | FetchPlugins<T>
  | FetchCommandProgress<T>
  | FetchCommandState<T>
  | FetchCommandValue<T>
  | FetchActivities<T>
  | FetchTransientView<T>
  | FetchTransientViews<T>
  | FetchServerStatus<T>;

// ======================== MUTATION ACTIONS ====================================

interface MutationAction<T = undefined> extends Action {
  type: MutatationType;
}

interface LoginAction<T = undefined> extends MutationAction<T> {
  type: MutatationType.LOGIN;
  dataType: unknown;
  variables: {
    username: string;
    password?: string;
    endpoint?: { host: string; port: number };
  };
}

interface UpdateItem<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_ITEM;
  dataType: ServerReturnType['update_item'];
  variables: ServerParameters['update_item'];
}

interface NewItem<T = undefined> extends MutationAction<T> {
  type: MutatationType.NEW_ITEM;
  dataType: ServerReturnType['new_item'];
  variables: ServerParameters['new_item'];
}

interface UpdateMetatags<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_METATAGS;
  dataType: ServerReturnType['update_metatags'];
  variables: ServerParameters['update_metatags'];
}

interface UpdateConfig<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_CONFIG;
  dataType: ServerReturnType['set_config'];
  variables: ServerParameters['set_config'];
}

interface StopQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.STOP_QUEUE;
  dataType: ServerReturnType['stop_queue'];
  variables: ServerParameters['stop_queue'];
}

interface StartQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.START_QUEUE;
  dataType: ServerReturnType['start_queue'];
  variables: ServerParameters['start_queue'];
}

interface ClearQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.CLEAR_QUEUE;
  dataType: ServerReturnType['clear_queue'];
  variables: ServerParameters['clear_queue'];
}

interface AddItemToQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_ITEM_TO_QUEUE;
  dataType: ServerReturnType['add_item_to_queue'];
  variables: ServerParameters['add_item_to_queue'];
}

interface RemoveItemFromQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.REMOVE_ITEM_FROM_QUEUE;
  dataType: ServerReturnType['remove_item_from_queue'];
  variables: ServerParameters['remove_item_from_queue'];
}

interface AddItemsToMetadataQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_ITEMS_TO_METADATA_QUEUE;
  dataType: ServerReturnType['add_items_to_metadata_queue'];
  variables: ServerParameters['add_items_to_metadata_queue'];
}

interface AddUrlsToDownloadQueue<T = undefined> extends MutationAction<T> {
  type: MutatationType.ADD_URLS_TO_DOWNLOAD_QUEUE;
  dataType: ServerReturnType['add_urls_to_download_queue'];
  variables: ServerParameters['add_urls_to_download_queue'];
}

interface PageReadEvent<T = undefined> extends MutationAction<T> {
  type: MutatationType.PAGE_READ_EVENT;
  dataType: ServerReturnType['page_read_event'];
  variables: ServerParameters['page_read_event'];
}

interface InstallPlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.INSTALL_PLUGIN;
  dataType: ServerReturnType['install_plugin'];
  variables: ServerParameters['install_plugin'];
}

interface DisablePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.DISABLE_PLUGIN;
  dataType: ServerReturnType['disable_plugin'];
  variables: ServerParameters['disable_plugin'];
}

interface RemovePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.REMOVE_PLUGIN;
  dataType: ServerReturnType['remove_plugin'];
  variables: ServerParameters['remove_plugin'];
}

interface UpdatePlugin<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_CONFIG;
  dataType: ServerReturnType['update_plugin'];
  variables: ServerParameters['update_plugin'];
}

interface OpenGallery<T = undefined> extends MutationAction<T> {
  type: MutatationType.OPEN_GALLERY;
  dataType: ServerReturnType['open_gallery'];
  variables: ServerParameters['open_gallery'];
}

interface UpdateFilters<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_FILTERS;
  dataType: ServerReturnType['update_filters'];
  variables: ServerParameters['update_filters'];
}

interface StartCommand<T = undefined> extends MutationAction<T> {
  type: MutatationType.START_COMMAND;
  dataType: ServerReturnType['start_command'];
  variables: ServerParameters['start_command'];
}

interface StopCommand<T = undefined> extends MutationAction<T> {
  type: MutatationType.STOP_COMMAND;
  dataType: ServerReturnType['stop_command'];
  variables: ServerParameters['stop_command'];
}

interface ResolvePathPattern<T = undefined> extends MutationAction<T> {
  type: MutatationType.RESOLVE_PATH_PATTERN;
  dataType: ServerReturnType['resolve_path_pattern'];
  variables: ServerParameters['resolve_path_pattern'];
}

interface ScanGalleries<T = undefined> extends MutationAction<T> {
  type: MutatationType.SCAN_GALLERIES;
  dataType: ServerReturnType['scan_galleries'];
  variables: ServerParameters['scan_galleries'];
}

interface TransientViewAction<T = undefined> extends MutationAction<T> {
  type: MutatationType.TRANSIENT_VIEW_ACTION;
  dataType: ServerReturnType['transient_view_action'];
  variables: ServerParameters['transient_view_action'];
}

interface TransientViewSubmitAction<T = undefined> extends MutationAction<T> {
  type: MutatationType.TRANSIENT_VIEW_SUBMIT_ACTION;
  dataType: ServerReturnType['transient_view_submit_action'];
  variables: ServerParameters['transient_view_submit_action'];
}

interface CreateTransientViewAction<T = undefined> extends MutationAction<T> {
  type: MutatationType.CREATE_TRANSIENT_VIEW;
  dataType: ServerReturnType['create_transient_view'];
  variables: ServerParameters['create_transient_view'];
}

interface UpdateTransientViewAction<T = undefined> extends MutationAction<T> {
  type: MutatationType.UPDATE_TRANSIENT_VIEW;
  dataType: ServerReturnType['update_transient_view'];
  variables: ServerParameters['update_transient_view'];
}

interface ReIndex<T = undefined> extends MutationAction<T> {
  type: MutatationType.REINDEX;
  dataType: ServerReturnType['reindex'];
  variables: ServerParameters['reindex'];
}

export type MutationActions<T = undefined> =
  | LoginAction<T>
  | NewItem<T>
  | UpdateItem<T>
  | UpdateMetatags<T>
  | UpdateConfig<T>
  | AddItemToQueue<T>
  | RemoveItemFromQueue<T>
  | AddItemsToMetadataQueue<T>
  | AddUrlsToDownloadQueue<T>
  | PageReadEvent<T>
  | StopQueue<T>
  | StartQueue<T>
  | UpdatePlugin<T>
  | RemovePlugin<T>
  | DisablePlugin<T>
  | InstallPlugin<T>
  | OpenGallery<T>
  | UpdateFilters<T>
  | StartCommand<T>
  | StopCommand<T>
  | ResolvePathPattern<T>
  | ScanGalleries<T>
  | TransientViewAction<T>
  | TransientViewSubmitAction<T>
  | CreateTransientViewAction<T>
  | UpdateTransientViewAction<T>
  | ReIndex<T>
  | ClearQueue<T>;

export type Actions<T = undefined> = MutationActions<T> | QueryActions<T>;

// ======================== SERVER QUERIES ====================================

export enum MomoType {
  SAME_MACHINE = 1,
}

interface MomoAction<T = undefined> extends Action {
  type: MomoType;
}

interface FetchSameMachine<T = undefined> extends MomoAction<T> {
  type: MomoType.SAME_MACHINE;
  dataType: {
    data: boolean;
  };
}

export type MomoActions<T = undefined> = FetchSameMachine<T>;
