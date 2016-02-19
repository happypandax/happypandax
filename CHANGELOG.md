*Happypanda v0.28*
- Improved perfomance of grid view significantly
- Galleries are now draggable
	+ It is now possible to add galleries to a list by dragging them to the list
- Improved metadata fetching accuracy from EH
- Improved gallery lists with new options
	+ It is now possible to enable several search options on per gallerylist basis
	+ A new *Enforce* option to enforce the gallerylist filter
- Improved gallery search
	+ New special namespaced tags: `read_count`, `date_added` and `last_read`
		+ Read more about them in the gallery searching guide
	+ New `<` less than and `>` greater than operator to be used with some special namespaced tags
		+ Read about it in the special namespaced tags section in the gallery searching guide
- Brought back the old way of gaining access to EX
	- Only to be used if you can't gain access to EX by logging in normally
- Added ability to specify arguments sent to viewer in settings (in the `Advanced` section)
	+ If when opening a gallery only the first image was viewable by your viewer, try change the arguments sent to the viewer
- Updated the database to version 0.24 with the addition of new gallerylist fields
- Moved regex search option to searchbar
- Added grid spacing option in settings (`Visual->Grid View`)
- Added folder and file extensions ignoring in settings (`Application->Ignore`)
	+ Folder and file extensions ignoring will work for the directory monitor and *Add gallery..* and *Populate from folder* gallery adding methods
- Added new default language: Chinese
- Improved and fixed URL parser in gallery-downloader
- Custom languages will now be parsed from filenames along with the default languages
- Tags are now sorted alphabetically everywhere
- Gallerylists in contextmenu are also now sorted
- Reason for why metdata fecthing failed is now shown in the failed-to-get-metadata-gallery popup
- The current search term will now be upkeeped (upkept?) when switching between views
- Disabled some tray messages on linux to prevent crash
- The current gallerylist context will now be shown on the statusbar
- The keys `del` and `shift + del` are now bound to gallery deletion
- Added *exclude/include in auto metadata fetcher* in contextmenu for selection
- Bug fixes:
	+ No thumbnails were created for images with incorrect extensions (namely png images with .jpg extension)
	+ Only accounts with access to EX were able to login
	+ Some filesystem events were not being detected
	+ Name parser was not parsing languages
	+ Some gallery attributes to not be added to the db on initial gallery creation
	+ Attempting to fetch metadata while an instance of auto metadata fetcher was already running caused an exception
	+ Gallery wasn't removed in view when removing from the duplicate-galleries popup
	+ Other minor bugs

*Happypanda v0.27*
- Many visual changes
	+ Including new ribbon indicating gallery type in gridview
- New sidebar widget:
	+ New feature: Gallery lists
	+ New feature: Artists list
	+ Moved *NS & Tags* treelist from settings to sidebar widget
- Metadata fetcher:
	+ Galleries with multiple hits found will now come last in the fetching process
	+ Added fallback system to fetch metadata from other sources than EH
		+ Currently supports panda.chaika.moe
- Gallery downloader should now be more tolerant to mistakes in URLs
- Added a "gallery source is missing" indicator in grid view
- Removed EH member_id and pass_hash in favor for EH login method
- Added new sort option: *last read*
- Added option to exclude/include gallery from auto metadata fetcher in the contextmenu
- Added general key shortcuts (read about the not so obvious shortcuts [here](https://github.com/Pewpews/happypanda/wiki/Keyboard-Shortcuts))
- Added support for new metafile: *HDoujin downloader*'s default into.txt file
- Added support for panda.chaika.moe URLs when fetching metadata
- Updated database to version 0.23:
	- Gallery lists addition
	- New unique indexes in some tables
	- Thumbnail paths are now relative (removing the need to rebuild thumbs when moving Happypanda folder)
- Settings:
	+ Added option to force support for high DPI displays
	+ Added option to control the gallery size in grid view
	+ Enabled most *Gallery* options in the *Visual* section for OSX
	+ Added options to customize gallery type ribbon colors
	+ Added options to set default gallery values
	+ Added a way to add custom languages in settings
	+ Added option to send deleted files  to recycle bin
	+ Added option to hide the sidebar widget on startup
- Bug fixes:
	+ Fixed a bug causing some external viewers to only be able to view the first image
	+ Fixed metadata disappearance bug (hopefully, for real this time!)
	+ Fixed decoding issues preventing some galleries from getting imported
	+ Fixed lots of critical database issues requiring a rebuild for updating users
	+ Fixed gallery downloading from g.e-hentai
	+ Fixed bug causing "Show in library" to not work properly
	+ Fixed a bug causing a hang while fetching metadata
	+ Fixed a bug causing autometadata fetcher to sometimes fail fetching for some galleries
	+ Fixed hand when checking for duplicates
	+ Fixed database rebuild issues
	+ Potentially fixed a bug preventing archives from being imported, courtesy of KuroiKitsu
	+ Many other minor bugs

*Happypanda v0.26*
- Startup is now slighty faster
- New redesigned gallery metadata window!
	+ New chapter view in the metadata window
	+ Artist field is now clickable to issue a search for galleries with same artist
- Some GUI changes
- New advanced gallery search **(make sure to read the search guide found in `Settings -> About -> Search Guide`)**
	+ Case sensitive searching
	+ Whole terms match searching
	+ Terms excluding
	+ New special namespaced tags (Read about them in `Settings -> About -> Search Guide`)
- New import/export database feature found in `Settings -> About -> Database`
- Added new column in `Skipped paths` window to show what reason caused a file to be skipped
- Gallery downloader
	+ Added new batch urls window to gallery downloader
	+ Gallery downloading from `panda.chaika.moe` is now using its new api
	+ Added context menu's to download items
	+ Added download progress on download items
	+ Doubleclicking on finished download items will open its containing folder
- Added autocomplete on the artist field in gallery edit dialog
- Activated the `last read` attribute on galleries
- Improved hash generation
- Introducing metafiles:
	+ Files containing gallery metadata in same folder/archive is now detected on import
	+ Only supports [eze](https://github.com/dnsev-h/eze)'s `info.json` files for now
- Settings
	+ Moved alot of options around. **Note: Some options will be reset**
	+ Reworded some options and fixed typos
	+ Enabled the `Database` tab in *About* section with import/export database feature
- Updated the database to version 0.22
	+ Database will now be backed up before upgrading
- Clicking on the tray icon ballon will now activate Happypanda
- Thumbnail regenerating
	+ Added confirmation popup when about to regenerate thumbnails
	+ Application restart is no longer required after regenerating thumbnails
	+ Added confirmation popup asking about if the thumbnail cache should be cleaned before regenerating
- Renamed `Random Gallery Opener` to `Open random gallery` and also moved it to the Gallery menu on the toolbar
- `Open random gallery` will now only pick a random gallery in current view.
	+ *E.g. switching to the favorite view will make it pick a random gallery among the favorites*
- Fixed bugs:
	+ Fixed a bug causing archives downloaded from g.e/ex to fail when trying to add to library
	+ Fixed a bug where fetching galleries from the database would sometimes throw an exception
	+ Fixed a bug causing people running from source to never see the new update notification
	+ Fixed some popup blur bug
	+ Fixed an annoyance where the text cursor would always move to the end when searching
	+ Fixed a bug where `Show in Folder` and `Open folder/archive` in gallery context menu was doing the same thing
	+ Fixed a bug where tags fetched from chaika included underscores
	+ Fixed bug where the notification widget would sometimes not show messages
	+ Fixed bug where chapters added to gallery with directory source would not open correctly

*Happypanda v0.25*
- Added *Show in folder* entry in gallery contextmenu
- Gallery popups
	+ A contextmenu will now be shown when you rightclick a gallery
	+ Added *Skip* button in the metadata gallery chooser popup (the one asking you which gallery you want to extract metadata from)
	+ The text in metadata gallery chooser popups will now wrap
	+ Added tooltips displaying title and artist when hovering galleries in some popups
- Settings
	+ A new button allowing you to recreate your thumbnail cache is now in *Settings* -> *Advanced* -> *Gallery*
	+ Added new tab *Downloader* in *Web* section
	+ Renamed *General* tab in *Web* section to *Metadata*
	+ Some options in settings will now show a tooltip explaining the option on hover
- You can now go back to previous or to next search terms with the two new buttons beside the search bar (hidden until you actually search something)
	+ Back and Forward keys has been bound to these two buttons (very OS dependent but something like `ALT + LEFT ARROW` etc.) Back and Forward buttons on your mouse should also probably work (*shrugs*)
	+ Added *Use current gallery link* checkbox option in *Web* section
- Toolbar
	+ Renamed *Misc* to *Tools*
	+ New *Scan for new galleries* entry in *Gallery*
	+ New *Gallery Downloader* entry in *Tools*
- Gallery downloading
	+ Supports archive and torrent downloading
	+ archives will be automatically imported while torrents will be sent to your torrent client
	+ Currently supports ex/g.e gallery urls and panda.chaika.moe gallery/archive urls
		- Note: downloading archives from ex/g.e will be handled the same way as if you did it in your browser, i.e. it will cost you GP/credits.
- Tray icon
	+ You can now manually check for a new update by right clicking on the tray icon
	+ Triggering the tray icon, i.e. clicking on it, will now activate (showing it) the Happypanda window
- Fixed bugs:
	+ Fixed a bug where skipped galleries/paths would get moved
	+ Fixed a bug where gallery archives/folders containing images with `.jpeg` and/or capitalized (`.JPG`, etc.) extensions were treated as invalid gallery sources, or causing the program to behave very weird if they managed to get imported somehow
	+ Fixed a bug where you couldn't search with the Regex option turned on
	+ Fixed a bug where changing gallery covers would fail if the previous cover was not deleted or found.
	+ Fixed a bug where non-existent monitored folders were not detected
	+ Fixed a bug in the user settings (*settings.ini*) parsing, hence the reset
	+ Fixed other minor misc. bugs

*Happypanda v0.24.1*
- Fixed bugs:
	+ Removing a gallery and its files should now work
	+ Popups was staying on top of all windows

*Happypanda v0.24*
- Mostly gui fixes/improvements
	+ Changed toolbar style and icons
	+ Added new native spinners
	+ Added spinner for the metadata fetching process
	+ Added spinner for initial load
	+ Added spinner for DB activity
	+ Removed sort contextmenu and added it to the toolbar
	+ Removed some space around galleries in grid view
	+ Added kinetic scrolling when scrolling with middlemouse button
- New DB Overview window and tab in settings dialog
	+ you can now see all namespaces and tags in the `Namespace and Tags` tab
- Pressing the return-key will now open selected galleries
- New options in settings dialog
	+ Make extracting archives before opening optional in `Application -> General`
	+ Open chapters sequentially or all at once in `Application -> General`
- Added a confirmation when closing while there is still DB activity to avoid data loss
- Added log file rotation
	+ When happypanda.log reaches `10 mb` a new file will be made (rotating between 3 files)
- Fixed bugs:
	+ Temporarily fixed a critical bug where galleries wouldn't load
	+ Fixed a bug where the tray icon would stay even after closing the application
	+ Fixed a bug where clicking on a tag with no namespace in the Gallery Metdata Popup would search the tag with a blank namespace
	+ Fixed a minor bug where when opening the settings dialog a small window would appear first in a split second

*Happypanda v0.23*
- Stability and perfomance increase for very large libraries
	+ Instant startup: Galleries are now lazily loaded
	+ Application now supports very large galleries (tested with 10k galleries)
	+ Gallery searching will now scale with amount of galleries (means, no freezes when searching)
	+ Same with adding new galleries.
- The gallery window appearing when you click on a gallery is now interactable
	+ Clicking on a link will open it in your default browser
	+ Clicking on a tag will search for the tag
- Added some animation and a spinner
- Fixed bugs:
	+ Fixed critical bug where slected galleries were not mapped properly. (Which sometimes resulted in wrong galleries being removed)
	+ Fixed a bug where pressing CTRL + A to select all galleries would tell that i has selected the total amount of galleries multipled by 3
	+ Fixed a bug where the notificationbar would sometiems not hide itself
	+ & other minor bugs

*Happypanda v0.22*
- Added support for .rar files.
	+ To enable rar support, specify the path to unrar in Settings -> Application -> General. Follow the instructions for your OS.
- Fixed most (if not all) gallery importing issues
- Added a way to populate form archive.
	+ Note: Subfolders will always be treated as galleries when populating from an archive.
- Fixed a bug where users who tries Happypanda for the first time would see the 'rebuilding galleries' dialog.
- & other misc. changes

*Happypanda v0.21*
- The application will now ask if you want to view skipped paths after searching for galleries
- Added 'delete successful' in the notificationbar
- Bugfixes:
	+ Fixed critical bug: Could not open chapters
		+ If your gallery still won't open then please try re-adding the gallery.
	+ Fixed bug: Covers for archives with no folder in-between were not being found
	+ & other minor bugs

*Happypanda v0.20*
- Added support for recursively importing of galleries (applies to archives)
	+ Directories in archives will now be noticed when importing
	+ Directories with archives as chapters will now be properly imported
- Added drag and drop feature for directories and archives
- Galleries that was unsuccesful during gallery fetching will now be displayed in a popup
- Added support for directory or archive ignoring
- Added support for changing gallery covers
- Added: move imported galleries to a specified folder feature
- Increased speed of Populate from folder and Add galleries...
- Improved title parser to now remove unneecessary whitespaces
- Improved gallery hashing to avoid unnecessary hashing
- Added 'Add archive' button in chapter dialog
- Popups will now center on parent window correctly
	+ It is now possible to move popups by leftclicking and dragging
	+ Added background blur effect when popups are shown
- The rebuild galleries popup will now show real progress
- Settings:
	+ Added new option: Treat subfolders as galleries
	+ Added new option: Move imported galleries
	+ Added new option: Scroll to new galleries (disabled)
	+ Added new option: Open random gallery chapters
	+ Added new option: Rename gallery source (disabled)
	+ Added new tab in Advanced section: Gallery
	+ Added new options: Gallery renamer (disabled)
	+ Added new tab in Application section: Ignore
	+ Enabled General tab in Application section
	+ Reenabled Display on gallery options
- Contextmenu:
	+ When selecting more galleries only options that apply to selected galleries will be shown
	+ It is now possible to favourite/Unfavourite selected galleries
	+ Reenabled removing of selected galleries
	+ Added: Advanced and Change cover
- Updated database to version 0.2
- Bugfixes:
	+ Fixed critical bug: not being able to add chapters
	+ Fixed bug: removing a chapter would always remove the first chapter
	+ Fixed bug: fetched metadata title and artist would not be formatted correctly
	+ & other minor bugs

*Happypanda v0.19*
- Improved stability
- Updated and fixed auto metadata fetcher:
    + Now twice as fast
    + No more need to restart application because it froze
    + Updated to support namespace fetching directly from the official API
- Improved tag autocompletion in gallery dialog
- Added a system tray to notify you about events such as auto metadata fetcher being done
- Sorting:
    + Added a new sort option: Publication Date
    + Added an indicator to the current sort option.
    + Your current sort option will now be saved
    + Increased pecision of date added
- Settings:
    + Added new options:
        * Continue auto metadata fetcher from where it left off
        * Use japanese title
    + Enabled option:
        * Auto add new galleries on startup
    + Removed options:
        * HTML Parsing or API
- Bugfixes:
    + Fixed critical bug: Fetching metadata from exhentai not working
    + Fixed critical bug: Duplicates were being created in database
    + Fixed a bug causing the update checker to always fail.

*Happypanda v0.18*
- Greatly improved stability
- Added numbers to show how many galleries are left when fetching for metadata
- Possibly fixed a bug causing the *"big changes are about to occur"* popup to never disappear
- Fixed auto metadata fetcher (did not work before)

*Happypanda v0.17*
- Improved UI
- Improved stability
- Improved the toolbar
-	+ Added a way to find duplicate galleries
	+ Added a random gallery opener
	+ Added a way to fetch metadata for all your galleries
- Added a way to automagically fetch metadata from g.e-/exhentai
	+ Fetching metadata is now safer, and should not get you banned
- Added a new sort option: Date added
- Added a place for gallery hashes in the database
- Added folder monitoring support
	+ You will now be informed when you rename, remove or add a gallery source in one of your monitored folders
	+ The application will scan for new galleries in all of your monitored folders on startup
- Added a new section in settings dialog: Application
	+ Added new options in settings dialog
	+ Enabled the 'General' tab in the Web section
- Bugfixes:
	+ Fixed a bug where you could only open the first chapter of a gallery
	+ Fixed a bug causing the application to crash when populating new galleries
	+ Fixed some issues occuring when adding archive files
	+ Fixed some issues occuring when editing galleries
	+ other small bugfixes
- Disabled gallery source type and external program viewer icons because of memory leak (will be reenabled in a later version)
- Cleaned up some code

*Happypanda v0.16*
- A more proper way to search for namespace and tags is now available
- Added support for external image viewers
- Added support for CBZ
- The settings button will now open up a real settings dialog
	+ Tons of new options are now available in the settings dialog
- Restyled the grid view
- Restyled the tooltip to now show other metadata in grid view
- Added troubleshoot, regex and search guides
- Fixed bugs:
	+ Application crashing when adding a gallery
	+ Application crashing when refreshing
	+ Namespace & tags not being shown correctly
	+ & other small bugs

*Happypanda v0.15*
- More options are now available in contextmenu when rightclicking a gallery
- It's now possible to add and remove chapters from a gallery
- Added a way to select more galleries
	+ More options are now available in contextmenu for selected galleries
- Added more columns to tableview
	+ Language
	+ Link
	+ Chapters
- Tweaked the grid view to reduce the lag when scrolling
- Added 1 more way to add galleries
- Already exisiting galleries will now be ignored
- Database will now try to auto update to newest version
- Updated Database to version 0.16 (breaking previous versions)
- Bugfixes

*Happypanda v0.14*
- New tableview. Switch easily between grid view and table view with the new button beside the searchbar
- Now able to add and read ZIP archives (You don't need to extract anymore).
	+ Added temp folder for when opening a chapter
- Changed icons to white icons
- Added tag autocomplete in series dialog
- Searchbar is now enabled for searching
	+ Autocomplete will complete series' titles
	+ Search for title or author
	+ Tag searching is only partially supported.
- Added sort options in contextmenu
- Title of series is now included in the 'Opening chapter' string
- Happypanda will now check for new version on startup
- Happypanda will now log errors.
	+ Added a --debug or -d option to create a detailed log
- Updated Database version to 0.15 (supports 0.14 & 0.13)
	+ Now with unique tag mappings
	+ A new metadata: times_read

*Happypanda v0.13*
- First public release