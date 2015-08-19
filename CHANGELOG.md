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