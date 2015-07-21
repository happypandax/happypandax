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