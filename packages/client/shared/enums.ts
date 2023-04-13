export enum ApplicationState {
  //: normal state
  Normal = 1,

  //: application is pending a restart
  Restarting = 2,

  //: application is pending a shutdown
  Shutdown = 3,

  //: application is currently updating
  Updating = 4
}


export enum TransientViewType {
  // Contains items to be added
  Import = 1,

  // Contains file paths
  File = 2,
}

export enum TransientViewAction {
  //: Process transient view
  Process = 1,

  //: Clear transient view from items
  Clear = 2,

  //: Remove transient view
  Remove = 3,

  //: Discard an item from the transient view, requires an item id
  Discard = 4,
}

export enum TransientViewSubmitAction {
  //: Send the contents of this transient view to an import transient view, requires a transient view id
  SendToView = 1,

  //: Send the contents of this transient view to the database
  SendToDatabase = 2,
}

export enum CommandState {
  // // command has not been put in any service yet
  OutOfService = 0,

  // // command has been put in a service (but not started or stopped yet)
  InService = 1,

  // // command has been scheduled to start
  InQueue = 2,

  // // command has been started
  Started = 3,

  // // command has finished succesfully
  Finished = 4,

  // // command has been forcefully stopped without finishing
  Stopped = 5,

  // // command has finished with an error
  Failed = 6,
}

export enum ItemType {
  // // Gallery
  Gallery = 1,
  // // Collection
  Collection = 2,
  // // Filter
  Filter = 3,
  // Page
  Page = 4,
  // Gallery Namespace
  Grouping = 5,
  // Gallery Title
  Title = 6,
  // Gallery Artist
  Artist = 7,
  // Category
  Category = 8,
  // Language
  Language = 9,
  // Status
  Status = 10,
  // Circle
  Circle = 11,
  // GalleryURL
  Url = 12,
  // Gallery Parody
  Parody = 13,
  // NamespaceTag
  NamespaceTag = 14,
  // Note
  Note = 15,
}

export enum ImageSize {
  // Original image size
  Original = 1,
  // Big image size
  Big = 2,
  // Medium image size
  Medium = 3,
  // Small image size
  Small = 4,
  // A maximum width of 2400
  x2400 = 10,
  // A maximum width of 2400
  x1600 = 11,
  // A maximum width of 1280
  x1280 = 12,
  // A maximum width of 960
  x960 = 13,
  // A maximum width of 768
  x768 = 14,
}

export enum ItemSort {
  // Gallery Random
  GalleryRandom = 1,
  // Gallery Title
  GalleryTitle = 2,
  // Gallery Artist Name
  GalleryArtist = 3,
  // Gallery Date Added
  GalleryDate = 4,
  // Gallery Date Published
  GalleryPublished = 5,
  // Gallery Last Read
  GalleryRead = 6,
  // Gallery Last Updated
  GalleryUpdated = 7,
  // Gallery Rating
  GalleryRating = 8,
  // Gallery Read Count
  GalleryReadCount = 9,
  // Gallery Page Count
  GalleryPageCount = 10,
  // Gallery Circle
  GalleryCircle = 11,

  // Grouping Random
  GroupingRandom = 50,
  // Grouping Name
  GroupingName = 51,
  // Grouping Date
  GroupingDate = 52,
  // Grouping Date
  GroupingGalleryCount = 53,

  // Artist Name
  ArtistName = 100,

  // Namespace
  NamespaceTagNamespace = 150,
  // Tag
  NamespaceTagTag = 151,

  // Tag
  FilterName = 200,

  // Circle Name
  CircleName = 250,

  // Parody Name
  ParodyName = 300,

  // Category Name
  CategoryName = 350,

  // Status Name
  StatusName = 400,

  // Language Name
  LanguageName = 450,

  // Collection Random
  CollectionRandom = 500,
  // Collection Name
  CollectionName = 501,
  // Collection Date Added
  CollectionDate = 502,
  // Collection Date Published
  CollectionPublished = 503,
  // Collection Gallery Count
  CollectionGalleryCount = 504,
}

export enum ProgressType {
  // Unknown
  Unknown = 1,
  // Network request
  Request = 2,
  // A check for new update
  CheckUpdate = 3,
  // Updating application
  UpdateApplication = 4,
  //: Scanning for items
  Scan = 5,
  //: Adding items to the database
  ItemAdd = 6,
  //: Adding items to the database
  ItemUpdate = 6,
  //: Removing items from the database
  ItemRemove = 8,
  //: A check for plugin update
  CheckPluginUpdate = 9,
  //: Upldating plugin
  UpdatePlugin = 10,
  //: Refreshing database
  DatabaseRefresh = 11

}

export enum PluginState {
  // Puporsely disabled
  Disabled = 0,
  // Unloaded because of dependencies, etc.
  Unloaded = 1,
  // Was just registered but not installed
  Registered = 2,
  // Allowed to be enabled
  Installed = 3,
  // Plugin is loaded and in use
  Enabled = 4,
  // Failed because of error
  Failed = 5,
}

export enum QueueType {
  // a queue for fetching metadata
  Metadata = 1,

  // a queue for downloading item
  Download = 2,
}

export enum Priority {
  // a low priority
  Low = 1,

  // a medium priority
  Medium = 2,

  // a high priority
  High = 3,
}

export enum ItemsKind {
  // Add all items
  all_items = 1,

  // Add items from library
  library_items = 2,

  // Add items from inbox
  inbox_items = 3,

  // Add items with missing tags
  tags_missing_items = 4,

  // Add items with missing tags from library
  tags_missing_library_items = 5,

  // Add items with missing tags from inbox
  tags_missing_inbox_items = 6,
}

export enum LogType {
  // Changelog
  Changelog = 1,

  // Download
  Download = 2,

  // Metadata
  Metadata = 3,
}

export enum NotificationType {
  // Meta
  Meta = 1,

  // Update
  Update = 2,

  // Restart
  Restart = 3,

  // Shutdown
  Shutdown = 4,

  // PluginUpdate
  PluginUpdate = 5,

  // Backup
  Backup = 6,

  // TrashSweeper
  TrashSweeper = 7,

  // Custom
  Custom = 99,
}

export enum DataMode {
  EDIT,
  READ_ONLY,
  DEFAULT,
}

export enum ReadingDirection {
  TopToBottom,
  LeftToRight,
}

export enum ItemFit {
  Height,
  Width,
  Contain,
  Auto,
}

export enum DrawerTab {
  Queue = 0,
  Metadata,
  Download,
  Selected,
  Recent,
}

export enum ViewType {
  // Contains all items except items in Trash
  All = 0,
  // Contains all items except items in Inbox and Trash
  Library = 1,
  // Contains only items in Inbox
  Inbox = 2,
}

export enum ActivityType {
  // unknown
  Unknown = 1,

  // metadata fetching activity
  Metadata = 2,

  // download activity
  Download = 3,

  // item data update activity
  ItemdataUpdate = 4,

  // item database update activity
  ItemUpdate = 5,

  // item database delete activity
  ItemDelete = 6,

  // item move  activity
  ItemMove = 7,

  // item similar items calculation activity
  ItemSimilar = 8,

  // item image generation activity
  Image = 9,

  // sync item source activity
  SyncWithSource = 10,
}
