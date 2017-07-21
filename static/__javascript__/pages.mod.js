	(function () {
		var utils = {};
		var widget = {};
		var client = __init__ (__world__.client).client;
		var Base = __init__ (__world__.client).Base;
		var ServerMsg = __init__ (__world__.client).ServerMsg;
		__nest__ (utils, '', __init__ (__world__.utils));
		__nest__ (widget, '', __init__ (__world__.widget));
		var BasePage = __class__ ('BasePage', [Base], {
			get main () {return __get__ (this, function (self) {
				moment.locale (utils.get_locale ());
			});},
			get config_save () {return __get__ (this, function (py_name) {
				// pass;
			});},
			get config_get () {return __get__ (this, function (py_name) {
				// pass;
			});}
		});
		var ApiPage = __class__ ('ApiPage', [Base], {
			get __init__ () {return __get__ (this, function (self, url) {
				if (typeof url == 'undefined' || (url != null && url .hasOwnProperty ("__kwargtrans__"))) {;
					var url = '/apiview';
				};
				__super__ (ApiPage, '__init__') (self, url);
			});},
			get get_type () {return __get__ (this, function (cls, s) {
				if (__in__ (s [0], tuple (["'", '"'])) && __in__ (s [len (s) - 1], tuple (["'", '"']))) {
					return s.__getslice__ (1, -(1), 1);
				}
				else if (__in__ (s.lower (), tuple (['none', 'null']))) {
					return null;
				}
				else {
					try {
						return int (s);
					}
					catch (__except0__) {
						if (isinstance (__except0__, ValueError)) {
							return s;
						}
						else {
							throw __except0__;
						}
					}
				}
			});},
			get call () {return __get__ (this, function (self) {
				var func_args = dict ({});
				var each_d = function (index, element) {
					var lichildren = $ (this).children ();
					var key = lichildren.eq (0).find ('input').val ();
					var value = lichildren.eq (1).find ('input').val ();
					if (key && value) {
						var value = value.strip ();
						if (value.startswith ('[') && value.endswith (']')) {
							var value = function () {
								var __accu0__ = [];
								for (var x of value.py_replace ('[', '').py_replace (']', '').py_split (',')) {
									if (x) {
										__accu0__.append (self.get_type (x.strip ()));
									}
								}
								return __accu0__;
							} ();
						}
						if (isinstance (value, str)) {
							var value = self.get_type (value);
						}
						func_args [key] = value;
					}
				};
				$ ('div#args > ul > li').each (each_d);
				var f_dict = dict ({'fname': $ ('#fname').val ()});
				f_dict.py_update (func_args);
				client.call (ServerMsg (list ([f_dict]), (function __lambda__ (msg) {
					return $ ('pre#json-receive').html (utils.syntax_highlight (JSON.stringify (msg, null, 4)));
				})));
				$ ('pre#json-send').html (utils.syntax_highlight (JSON.stringify (client._last_msg ['msg'], null, 4)));
			});},
			get add_kwarg () {return __get__ (this, function (self) {
				$ ('div#args > ul').append ("\n            <li>\n            <div class='col-xs-6'>\n            <input type='text', placeholder='keyword' class='form-control'>\n            </div>\n            <div class='col-xs-6'>\n            <input type='text', placeholder='value' class='form-control'>\n            </div>\n            </li>\n            ");
			});}
		});
		var LibraryPage = __class__ ('LibraryPage', [Base], {
			get __init__ () {return __get__ (this, function (self, py_name, url) {
				if (typeof py_name == 'undefined' || (py_name != null && py_name .hasOwnProperty ("__kwargtrans__"))) {;
					var py_name = 'Library';
				};
				if (typeof url == 'undefined' || (url != null && url .hasOwnProperty ("__kwargtrans__"))) {;
					var url = '/library';
				};
				__super__ (LibraryPage, '__init__') (self, url);
				self.py_name = py_name;
				self.py_items = dict ({});
				self.artists = dict ({});
				self.tags = dict ({});
				self.gfilters = dict ({});
				self.item_limit = 100;
				self._page_limit = 10;
				self._page_list = list ([]);
				self.current_page = 1;
				self._properties = dict ({'search_query': '', 'view': 'Gallery', 'sort': 'Title', 'sort_order': 'Ascending', 'group': false, 'iscroll': false});
				self.grid = utils.Grid ('#items', '#items .gallery', __kwargtrans__ ({gutter: 20}));
			});},
			get context_nav () {return __get__ (this, function (self) {
				var args = tuple ([].slice.apply (arguments).slice (1));
				var ctx_links = function () {
					var __accu0__ = [];
					for (var x of args) {
						__accu0__.append (dict ({'name': x [0], 'url': x [1]}));
					}
					return __accu0__;
				} ();
				self.compile ('#context-nav-t', '#item-main', __kwargtrans__ ({prepend: true, context_links: ctx_links}));
			});},
			get update_context () {return __get__ (this, function (self) {
				return ;
				self.context_nav (...self._context_link);
			});},
			get add_context () {return __get__ (this, function (self, py_name, url) {
				self._context_link.append (tuple ([py_name, url]));
				self.update_context ();
			});},
			get reset_context () {return __get__ (this, function (self) {
				self._context_link = list ([tuple ([self.py_name, self.url])]);
			});},
			get set_properties () {return __get__ (this, function (self) {
				$ ('#current-view').text (self._properties ['view']);
			});},
			get get_property () {return __get__ (this, function (self, p) {
				var r = self._properties [p];
				if (p == 'view' && self._properties ['group'] && r == 'Gallery') {
					var r = 'Grouping';
				}
				return r;
			});},
			get main () {return __get__ (this, function (self) {
				__super__ (LibraryPage, 'main') (self);
				self.fetch_gfilters ();
				self.show_pagination ();
			});},
			get update_sidebar () {return __get__ (this, function (self, lists, tags, artist_obj) {
				if (typeof lists == 'undefined' || (lists != null && lists .hasOwnProperty ("__kwargtrans__"))) {;
					var lists = null;
				};
				if (typeof tags == 'undefined' || (tags != null && tags .hasOwnProperty ("__kwargtrans__"))) {;
					var tags = null;
				};
				if (typeof artist_obj == 'undefined' || (artist_obj != null && artist_obj .hasOwnProperty ("__kwargtrans__"))) {;
					var artist_obj = dict ({});
				};
				if (arguments.length) {
					var __ilastarg0__ = arguments.length - 1;
					if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
						var __allkwargs0__ = arguments [__ilastarg0__--];
						for (var __attrib0__ in __allkwargs0__) {
							switch (__attrib0__) {
								case 'self': var self = __allkwargs0__ [__attrib0__]; break;
								case 'lists': var lists = __allkwargs0__ [__attrib0__]; break;
								case 'tags': var tags = __allkwargs0__ [__attrib0__]; break;
								case 'artist_obj': var artist_obj = __allkwargs0__ [__attrib0__]; break;
							}
						}
					}
				}
				else {
				}
				if (artist_obj !== null) {
					var artist_data = list ([]);
					for (var a of __i__ (artist_obj)) {
						artist_data.append (dict ({'name': artist_obj [a] ['name'], 'count': artist_obj [a] ['count']}));
					}
					self.compile ('#side-artists-t', '#side-artists', __kwargtrans__ ({side_artists: artist_data}));
				}
			});},
			get update_pagination () {return __get__ (this, function (self, from_page) {
				if (typeof from_page == 'undefined' || (from_page != null && from_page .hasOwnProperty ("__kwargtrans__"))) {;
					var from_page = 1;
				};
				self.current_page = from_page;
				var back_disabled = false;
				var next_disabled = false;
				if (from_page - 1 == 0) {
					var back_disabled = true;
				}
				if (from_page == len (self._page_list)) {
					var next_disabled = true;
				}
				var half_limit = int (self._page_limit / 2);
				var l_index = from_page - half_limit;
				var r_index = (from_page + half_limit) + 1;
				if (r_index > len (self._page_list)) {
					var r_index = len (self._page_list);
					var l_index = len (self._page_list) - (self._page_limit + 1);
				}
				if (l_index < 0) {
					var l_index = 0;
					var r_index = self._page_limit;
				}
				var current_pages = self._page_list.__getslice__ (l_index, r_index, 1);
				var pages = list ([]);
				for (var n of current_pages) {
					pages.append (dict ({'number': n, 'active': n == from_page}));
				}
				self.show_items (__kwargtrans__ ({page: from_page}));
				self.compile ('#item-pagination-t', '.item-pagination', __kwargtrans__ ({pages: pages, back_button: !(back_disabled), next_button: !(next_disabled), back_number: from_page - 1, next_number: from_page + 1}));
			});},
			get show_pagination () {return __get__ (this, function (self, data, error) {
				if (typeof data == 'undefined' || (data != null && data .hasOwnProperty ("__kwargtrans__"))) {;
					var data = null;
				};
				if (typeof error == 'undefined' || (error != null && error .hasOwnProperty ("__kwargtrans__"))) {;
					var error = null;
				};
				if (data !== null && !(error)) {
					var pages = data ['count'] / self.item_limit;
					if (pages < 1) {
						var pages = 1;
					}
					if (__mod__ (pages, 1) == 0) {
						var pages = int (pages);
					}
					else {
						var pages = int (pages) + 1;
					}
					self._page_list = range (1, pages + 1);
					self.update_pagination ();
				}
				else if (error) {
					// pass;
				}
				else {
					client.call_func ('get_view_count', self.show_pagination, __kwargtrans__ ({item_type: self.get_property ('view'), search_query: self.get_property ('search_query')}));
				}
			});},
			get fetch_gfilters () {return __get__ (this, function (self, data, error) {
				if (typeof data == 'undefined' || (data != null && data .hasOwnProperty ("__kwargtrans__"))) {;
					var data = null;
				};
				if (typeof error == 'undefined' || (error != null && error .hasOwnProperty ("__kwargtrans__"))) {;
					var error = null;
				};
				if (data !== null && !(error)) {
					var lists_data = list ([]);
					for (var gl of data) {
						self.gfilters [gl ['id']] = gl;
						lists_data.append (dict ({'name': gl ['name']}));
					}
					self.compile ('#side-lists-t', '#side-lists .list-group', __kwargtrans__ ({append: true, side_lists: lists_data}));
				}
				else if (error) {
					// pass;
				}
				else {
					client.call_func ('get_items', self.fetch_gfilters, __kwargtrans__ ({item_type: 'galleryfilter'}));
				}
			});},
			get show_items () {return __get__ (this, function (self, data, error, page) {
				if (typeof data == 'undefined' || (data != null && data .hasOwnProperty ("__kwargtrans__"))) {;
					var data = null;
				};
				if (typeof error == 'undefined' || (error != null && error .hasOwnProperty ("__kwargtrans__"))) {;
					var error = null;
				};
				if (typeof page == 'undefined' || (page != null && page .hasOwnProperty ("__kwargtrans__"))) {;
					var page = null;
				};
				if (arguments.length) {
					var __ilastarg0__ = arguments.length - 1;
					if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
						var __allkwargs0__ = arguments [__ilastarg0__--];
						for (var __attrib0__ in __allkwargs0__) {
							switch (__attrib0__) {
								case 'self': var self = __allkwargs0__ [__attrib0__]; break;
								case 'data': var data = __allkwargs0__ [__attrib0__]; break;
								case 'error': var error = __allkwargs0__ [__attrib0__]; break;
								case 'page': var page = __allkwargs0__ [__attrib0__]; break;
							}
						}
					}
				}
				else {
				}
				if (__t__ (!__t__ ((page)))) {
					var page = self.current_page;
				}
				if (__t__ (__t__ (data !== null) && !__t__ ((error)))) {
					self.set_properties ();
					self.artists.py_clear ();
					var _view = self.get_property ('view');
					var py_items = list ([]);
					if (__t__ (_view == 'Gallery')) {
						if (__t__ (!__t__ ((self._properties ['iscroll'])))) {
							self.py_items.py_clear ();
							$ ('#items').empty ();
						}
						for (var g of __i__ (data)) {
							var g_obj = widget.Gallery ('medium', g);
							self.py_items [g ['id']] = g_obj;
							py_items.append (g_obj);
							for (var a of __i__ (g ['artists'])) {
								var a_id = a ['id'];
								if (__t__ (__in__ (a_id, self.artists))) {
									self.artists [a_id] ['count']++;
								}
								else {
									self.artists [a_id] = a;
									self.artists [a_id] ['count'] = 1;
								}
							}
						}
					}
					self.update_sidebar (__kwargtrans__ ({artist_obj: self.artists}));
					if (__t__ (py_items)) {
						for (var i of __i__ (py_items)) {
							i.compile ('#items', __kwargtrans__ ({append: true}));
							i.fetch_thumb ();
						}
					}
					if (__t__ (!__t__ ((py_items)))) {
						self.show_nothing ('#items');
					}
					self.grid.reload ();
					self.grid.layout ();
				}
				else if (__t__ (error)) {
					// pass;
				}
				else {
					var view = self.get_property ('view');
					client.call_func ('library_view', self.show_items, __kwargtrans__ ({item_type: view, limit: self.item_limit, page: page - 1, search_query: self._properties ['search_query']}));
				}
			});},
			get set_property () {return __get__ (this, function (self, p, v) {
				self._properties [p] = v;
				self.show_pagination ();
			});},
			get update_search_query () {return __get__ (this, function (self) {
				var sq = $ ('#search').val ();
				self.log ('search query: {}'.format (sq));
				self._properties ['search_query'] = sq;
				self.show_pagination ();
			});},
			get show_nothing () {return __get__ (this, function (self, target_el) {
				self.compile ('#nothing-t', target_el);
			});}
		});
		var InboxPage = __class__ ('InboxPage', [BasePage], {
			get __init__ () {return __get__ (this, function (self, py_name, url) {
				if (typeof py_name == 'undefined' || (py_name != null && py_name .hasOwnProperty ("__kwargtrans__"))) {;
					var py_name = 'Inbox';
				};
				if (typeof url == 'undefined' || (url != null && url .hasOwnProperty ("__kwargtrans__"))) {;
					var url = '/inbox';
				};
				__super__ (InboxPage, '__init__') (self, py_name, url);
			});}
		});
		var FavortiesPage = __class__ ('FavortiesPage', [BasePage], {
			get __init__ () {return __get__ (this, function (self, py_name, url) {
				if (typeof py_name == 'undefined' || (py_name != null && py_name .hasOwnProperty ("__kwargtrans__"))) {;
					var py_name = 'Favorites';
				};
				if (typeof url == 'undefined' || (url != null && url .hasOwnProperty ("__kwargtrans__"))) {;
					var url = '/fav';
				};
				__super__ (FavortiesPage, '__init__') (self, py_name, url);
			});}
		});
		var GalleryPage = __class__ ('GalleryPage', [Base], {
			get __init__ () {return __get__ (this, function (self) {
				__super__ (GalleryPage, '__init__') (self);
				self.obj = null;
				self.g_id = self.url.path ().py_split ('/') [2];
			});},
			get main () {return __get__ (this, function (self) {
				__super__ (GalleryPage, 'main') (self);
				self.show_gallery ();
			});},
			get show_gallery () {return __get__ (this, function (self, data, error) {
				if (typeof data == 'undefined' || (data != null && data .hasOwnProperty ("__kwargtrans__"))) {;
					var data = null;
				};
				if (typeof error == 'undefined' || (error != null && error .hasOwnProperty ("__kwargtrans__"))) {;
					var error = null;
				};
				if (data !== null && !(error)) {
					self.obj = widget.Gallery ('page', data);
					self.compile ('#gallery-t', '.breadcrumb', __kwargtrans__ ({after: true, thumb: '/static/img/default.png', title: self.obj.title (), artists: data ['artists'], lang: 'test', inbox: data ['inbox'], fav: data ['fav'], published: moment.unix (data ['pub_date']).format ('LL'), updated: moment.unix (data ['last_updated']).format ('LLL'), read: moment.unix (data ['last_read']).format ('LLL'), added: moment.unix (data ['timestamp']).format ('LLL'), rel_added: moment.unix (data ['timestamp']).fromNow (), rel_updated: moment.unix (data ['last_updated']).fromNow (), rel_read: moment.unix (data ['last_read']).fromNow ()}));
					widget.Thumbnail ('#profile', 'big', 'Gallery', self.obj ['id']).fetch_thumb ();
				}
				else if (error) {
					// pass;
				}
				else {
					client.call_func ('get_item', self.show_gallery, __kwargtrans__ ({item_type: 'Gallery', item_id: int (self.g_id)}));
				}
			});}
		});
		var _pages = dict ({});
		var init_page = function (p, cls) {
			var kwargs = dict ();
			if (arguments.length) {
				var __ilastarg0__ = arguments.length - 1;
				if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
					var __allkwargs0__ = arguments [__ilastarg0__--];
					for (var __attrib0__ in __allkwargs0__) {
						switch (__attrib0__) {
							case 'p': var p = __allkwargs0__ [__attrib0__]; break;
							case 'cls': var cls = __allkwargs0__ [__attrib0__]; break;
							default: kwargs [__attrib0__] = __allkwargs0__ [__attrib0__];
						}
					}
					delete kwargs.__kwargtrans__;
				}
				var args = tuple ([].slice.apply (arguments).slice (2, __ilastarg0__ + 1));
			}
			else {
				var args = tuple ();
			}
			_pages [p] = cls (...args, __kwargtrans__ (kwargs));
			return _pages [p];
		};
		var get_page = function (p) {
			return _pages [p];
		};
		var init = function () {
			$ ('div[onload]').trigger ('onload');
		};
		$ (document).ready (init);
		__pragma__ ('<use>' +
			'client' +
			'utils' +
			'widget' +
		'</use>')
		__pragma__ ('<all>')
			__all__.ApiPage = ApiPage;
			__all__.Base = Base;
			__all__.BasePage = BasePage;
			__all__.FavortiesPage = FavortiesPage;
			__all__.GalleryPage = GalleryPage;
			__all__.InboxPage = InboxPage;
			__all__.LibraryPage = LibraryPage;
			__all__.ServerMsg = ServerMsg;
			__all__._pages = _pages;
			__all__.client = client;
			__all__.get_page = get_page;
			__all__.init = init;
			__all__.init_page = init_page;
		__pragma__ ('</all>')
	}) ();
