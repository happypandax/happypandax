import type ServerService from '../services/server';
import type { RequestOptions } from '../server/requests';
import { FieldPath, ServerSortIndex } from './types';

export enum QueryType {
    PROFILE = '/api/profile',
    PAGES = '/api/pages',
    LIBRARY = '/api/library',
    ITEMS = '/api/items',
    ITEM = '/api/item',
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
    LOGIN = '/api/login',
    UPDATE_ITEM = '/api/item',
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
}

// ======================== ACTIONS ====================================

export type ServiceParameters = {
    [K in keyof ServerService]:
    | {
        __options?: RequestOptions;
    }
    | Parameters<
        ServerService[K] extends (...args: any[]) => any
        ? ServerService[K]
        : never
    >[0];
};

export type ServiceReturnType = {
    [K in keyof ServerService]: Unwrap<
        ReturnType<
            ServerService[K] extends (...args: any[]) => any
            ? ServerService[K]
            : never
        >
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
    variables: ServiceParameters['sort_indexes'];
}

interface FetchProfile<T = undefined> extends QueryAction<T> {
    type: QueryType.PROFILE;
    dataType: ServiceReturnType['profile'];
    variables: ServiceParameters['profile'];
}

interface FetchItem<T = undefined> extends QueryAction<T> {
    type: QueryType.ITEM;
    dataType: Record<string, any>;
    variables: Omit<ServiceParameters['item'], 'fields'> & {
        fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
    };
}

interface FetchItems<T = undefined> extends QueryAction<T> {
    type: QueryType.ITEMS;
    dataType: ServiceReturnType['items'];
    variables: Omit<ServiceParameters['items'], 'fields'> & {
        fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
    };
}

interface FetchSearchItems<T = undefined> extends QueryAction<T> {
    type: QueryType.ITEMS;
    dataType: ServiceReturnType['search_items'];
    variables: Omit<ServiceParameters['search_items'], 'fields'> & {
        fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
    };
}

interface FetchLibrary<T = undefined> extends QueryAction<T> {
    type: QueryType.LIBRARY;
    dataType: ServiceReturnType['library'];
    variables: Omit<ServiceParameters['library'], 'fields'> & {
        fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
    };
}

interface FetchRelatedItems<T = undefined> extends QueryAction<T> {
    type: QueryType.RELATED_ITEMS;
    dataType: ServiceReturnType['related_items'];
    variables: Omit<ServiceParameters['related_items'], 'fields'> & {
        fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
    };
}

interface FetchPages<T = undefined> extends QueryAction<T> {
    type: QueryType.PAGES;
    dataType: ServiceReturnType['pages'];
    variables: Omit<ServiceParameters['pages'], 'fields'> & {
        fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
    };
}

interface FetchSimilar<T = undefined> extends QueryAction<T> {
    type: QueryType.SIMILAR;
    dataType: ServiceReturnType['similar'];
    variables: Omit<ServiceParameters['similar'], 'fields'> & {
        fields?: [T] extends [undefined] ? FieldPath[] : DeepPickPathPlain<T>[];
    };
}

interface FetchSearchLabels<T = undefined> extends QueryAction<T> {
    type: QueryType.SEARCH_LABELS;
    dataType: ServiceReturnType['search_labels'];
    variables: ServiceParameters['search_labels'];
}

interface FetchQueueItems<T = undefined> extends QueryAction<T> {
    type: QueryType.QUEUE_ITEMS;
    dataType: ServiceReturnType['queue_items'];
    variables: ServiceParameters['queue_items'];
}
interface FetchQueueState<T = undefined> extends QueryAction<T> {
    type: QueryType.QUEUE_STATE;
    dataType: ServiceReturnType['queue_state'];
    variables: ServiceParameters['queue_state'];
}

interface FetchLog<T = undefined> extends QueryAction<T> {
    type: QueryType.LOG;
    dataType: ServiceReturnType['log'];
    variables: ServiceParameters['log'];
}

interface FetchDownloadInfo<T = undefined> extends QueryAction<T> {
    type: QueryType.DOWNLOAD_INFO;
    dataType: ServiceReturnType['download_info'];
    variables: ServiceParameters['download_info'];
}

interface FetchMetadataInfo<T = undefined> extends QueryAction<T> {
    type: QueryType.METADATA_INFO;
    dataType: ServiceReturnType['metadata_info'];
    variables: ServiceParameters['metadata_info'];
}

interface FetchConfig<T = undefined> extends QueryAction<T> {
    type: QueryType.CONFIG;
    dataType: ServiceReturnType['config'];
    variables: ServiceParameters['config'];
}

interface FetchPlugin<T = undefined> extends QueryAction<T> {
    type: QueryType.PLUGIN;
    dataType: ServiceReturnType['plugin'];
    variables: ServiceParameters['plugin'];
}

interface FetchPluginUpdate<T = undefined> extends QueryAction<T> {
    type: QueryType.PLUGIN_UPDATE;
    dataType: ServiceReturnType['check_plugin_update'];
    variables: ServiceParameters['check_plugin_update'];
}

interface FetchPlugins<T = undefined> extends QueryAction<T> {
    type: QueryType.PLUGINS;
    dataType: ServiceReturnType['list_plugins'];
    variables: ServiceParameters['list_plugins'];
}

interface FetchCommandProgress<T = undefined> extends QueryAction<T> {
    type: QueryType.COMMAND_PROGRESS;
    dataType: ServiceReturnType['command_progress'];
    variables: ServiceParameters['command_progress'];
}

interface FetchCommandState<T = undefined> extends QueryAction<T> {
    type: QueryType.COMMAND_STATE;
    dataType: ServiceReturnType['command_state'];
    variables: ServiceParameters['command_state'];
}

interface FetchCommandValue<T = undefined> extends QueryAction<T> {
    type: QueryType.COMMAND_VALUE;
    dataType: ServiceReturnType['command_value'];
    variables: ServiceParameters['command_value'];
}
interface FetchActivities<T = undefined> extends QueryAction<T> {
    type: QueryType.ACTIVITIES;
    dataType: ServiceReturnType['activities'];
    variables: ServiceParameters['activities'];
}

interface FetchTransientView<T = undefined> extends QueryAction<T> {
    type: QueryType.TRANSIENT_VIEW;
    dataType: ServiceReturnType['transient_view'];
    variables: ServiceParameters['transient_view'];
}

interface FetchTransientViews<T = undefined> extends QueryAction<T> {
    type: QueryType.TRANSIENT_VIEWS;
    dataType: ServiceReturnType['transient_views'];
    variables: ServiceParameters['transient_views'];
}

export type QueryActions<T = undefined> =
    | FetchProfile<T>
    | FetchItem<T>
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
    dataType: ServiceReturnType['login'];
    variables: {
        username: string;
        password?: string;
        endpoint?: { host: string; port: number };
    };
}

interface UpdateItem<T = undefined> extends MutationAction<T> {
    type: MutatationType.UPDATE_ITEM;
    dataType: ServiceReturnType['update_item'];
    variables: ServiceParameters['update_item'];
}

interface UpdateMetatags<T = undefined> extends MutationAction<T> {
    type: MutatationType.UPDATE_METATAGS;
    dataType: ServiceReturnType['update_metatags'];
    variables: ServiceParameters['update_metatags'];
}

interface UpdateConfig<T = undefined> extends MutationAction<T> {
    type: MutatationType.UPDATE_CONFIG;
    dataType: ServiceReturnType['set_config'];
    variables: ServiceParameters['set_config'];
}

interface StopQueue<T = undefined> extends MutationAction<T> {
    type: MutatationType.STOP_QUEUE;
    dataType: ServiceReturnType['stop_queue'];
    variables: ServiceParameters['stop_queue'];
}

interface StartQueue<T = undefined> extends MutationAction<T> {
    type: MutatationType.START_QUEUE;
    dataType: ServiceReturnType['start_queue'];
    variables: ServiceParameters['start_queue'];
}

interface ClearQueue<T = undefined> extends MutationAction<T> {
    type: MutatationType.CLEAR_QUEUE;
    dataType: ServiceReturnType['clear_queue'];
    variables: ServiceParameters['clear_queue'];
}

interface AddItemToQueue<T = undefined> extends MutationAction<T> {
    type: MutatationType.ADD_ITEM_TO_QUEUE;
    dataType: ServiceReturnType['add_item_to_queue'];
    variables: ServiceParameters['add_item_to_queue'];
}

interface RemoveItemFromQueue<T = undefined> extends MutationAction<T> {
    type: MutatationType.REMOVE_ITEM_FROM_QUEUE;
    dataType: ServiceReturnType['remove_item_from_queue'];
    variables: ServiceParameters['remove_item_from_queue'];
}

interface AddItemsToMetadataQueue<T = undefined> extends MutationAction<T> {
    type: MutatationType.ADD_ITEMS_TO_METADATA_QUEUE;
    dataType: ServiceReturnType['add_items_to_metadata_queue'];
    variables: ServiceParameters['add_items_to_metadata_queue'];
}

interface AddUrlsToDownloadQueue<T = undefined> extends MutationAction<T> {
    type: MutatationType.ADD_URLS_TO_DOWNLOAD_QUEUE;
    dataType: ServiceReturnType['add_urls_to_download_queue'];
    variables: ServiceParameters['add_urls_to_download_queue'];
}

interface PageReadEvent<T = undefined> extends MutationAction<T> {
    type: MutatationType.PAGE_READ_EVENT;
    dataType: ServiceReturnType['page_read_event'];
    variables: ServiceParameters['page_read_event'];
}

interface InstallPlugin<T = undefined> extends MutationAction<T> {
    type: MutatationType.INSTALL_PLUGIN;
    dataType: ServiceReturnType['install_plugin'];
    variables: ServiceParameters['install_plugin'];
}

interface DisablePlugin<T = undefined> extends MutationAction<T> {
    type: MutatationType.DISABLE_PLUGIN;
    dataType: ServiceReturnType['disable_plugin'];
    variables: ServiceParameters['disable_plugin'];
}

interface RemovePlugin<T = undefined> extends MutationAction<T> {
    type: MutatationType.REMOVE_PLUGIN;
    dataType: ServiceReturnType['remove_plugin'];
    variables: ServiceParameters['remove_plugin'];
}

interface UpdatePlugin<T = undefined> extends MutationAction<T> {
    type: MutatationType.UPDATE_CONFIG;
    dataType: ServiceReturnType['update_plugin'];
    variables: ServiceParameters['update_plugin'];
}

interface OpenGallery<T = undefined> extends MutationAction<T> {
    type: MutatationType.OPEN_GALLERY;
    dataType: ServiceReturnType['open_gallery'];
    variables: ServiceParameters['open_gallery'];
}

interface UpdateFilters<T = undefined> extends MutationAction<T> {
    type: MutatationType.UPDATE_FILTERS;
    dataType: ServiceReturnType['update_filters'];
    variables: ServiceParameters['update_filters'];
}

interface StartCommand<T = undefined> extends MutationAction<T> {
    type: MutatationType.START_COMMAND;
    dataType: ServiceReturnType['start_command'];
    variables: ServiceParameters['start_command'];
}

interface StopCommand<T = undefined> extends MutationAction<T> {
    type: MutatationType.STOP_COMMAND;
    dataType: ServiceReturnType['stop_command'];
    variables: ServiceParameters['stop_command'];
}

interface ResolvePathPattern<T = undefined> extends MutationAction<T> {
    type: MutatationType.RESOLVE_PATH_PATTERN;
    dataType: ServiceReturnType['resolve_path_pattern'];
    variables: ServiceParameters['resolve_path_pattern'];
}

interface ScanGalleries<T = undefined> extends MutationAction<T> {
    type: MutatationType.SCAN_GALLERIES;
    dataType: ServiceReturnType['scan_galleries'];
    variables: ServiceParameters['scan_galleries'];
}

interface TransientViewApply<T = undefined> extends MutationAction<T> {
    type: MutatationType.TRANSIENT_VIEW_ACTION;
    dataType: ServiceReturnType['transient_view_apply'];
    variables: ServiceParameters['transient_view_apply'];
}

export type MutationActions<T = undefined> =
    | LoginAction<T>
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
    | TransientViewApply<T>
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
        data: boolean
    };
}

export type MomoActions<T = undefined> = FetchSameMachine<T>