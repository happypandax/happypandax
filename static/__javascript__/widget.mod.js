	__nest__ (
		__all__,
		'widget', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var client = __init__ (__world__.client).client;
					var thumbclient = __init__ (__world__.client).thumbclient;
					var Base = __init__ (__world__.client).Base;
					var Command = __init__ (__world__.client).Command;
					var Widget = __class__ ('Widget', [Base], {
						get __init__ () {return __get__ (this, function (self, source_el) {
							__super__ (Widget, '__init__') (self);
							self._source_el = source_el;
							self.node = null;
						});},
						get compile () {return __get__ (this, function (self, target_el, after, before, append, prepend) {
							if (typeof after == 'undefined' || (after != null && after .hasOwnProperty ("__kwargtrans__"))) {;
								var after = null;
							};
							if (typeof before == 'undefined' || (before != null && before .hasOwnProperty ("__kwargtrans__"))) {;
								var before = null;
							};
							if (typeof append == 'undefined' || (append != null && append .hasOwnProperty ("__kwargtrans__"))) {;
								var append = null;
							};
							if (typeof prepend == 'undefined' || (prepend != null && prepend .hasOwnProperty ("__kwargtrans__"))) {;
								var prepend = null;
							};
							var data = dict ();
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'target_el': var target_el = __allkwargs0__ [__attrib0__]; break;
											case 'after': var after = __allkwargs0__ [__attrib0__]; break;
											case 'before': var before = __allkwargs0__ [__attrib0__]; break;
											case 'append': var append = __allkwargs0__ [__attrib0__]; break;
											case 'prepend': var prepend = __allkwargs0__ [__attrib0__]; break;
											default: data [__attrib0__] = __allkwargs0__ [__attrib0__];
										}
									}
									delete data.__kwargtrans__;
								}
							}
							else {
							}
							self.node = __super__ (Widget, 'compile') (self, self._source_el, target_el, __kwargtrans__ (__merge__ ({after: after, before: before, append: append, prepend: prepend}, data)));
						});},
						get get_node () {return __get__ (this, function (self) {
							if (!(self.node)) {
								self.node = $ (self._source_el);
							}
							return self.node;
						});}
					});
					var Thumbnail = __class__ ('Thumbnail', [Widget], {
						get __init__ () {return __get__ (this, function (self, source_el, size_type, item_type, id) {
							__super__ (Thumbnail, '__init__') (self, source_el);
							self.thumbclient = thumbclient;
							self.item_type = item_type;
							self.size_type = size_type;
							self.id = id;
							self._thumbs = dict ({'Big': null, 'Medium': null, 'Small': null});
							self._thumbsize = null;
						});},
						get _fetch_thumb () {return __get__ (this, function (self, data, error, size) {
							if (typeof data == 'undefined' || (data != null && data .hasOwnProperty ("__kwargtrans__"))) {;
								var data = null;
							};
							if (typeof error == 'undefined' || (error != null && error .hasOwnProperty ("__kwargtrans__"))) {;
								var error = null;
							};
							if (typeof size == 'undefined' || (size != null && size .hasOwnProperty ("__kwargtrans__"))) {;
								var size = 'Big';
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
											case 'size': var size = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
							}
							else {
							}
							if (__t__ (__t__ (data !== null) && !__t__ ((error)))) {
								var cmd_id = data [str (self.id)];
								var cmd = Command (cmd_id);
								self._thumbs [self._thumbsize] = cmd;
								cmd.set_callback (self._set_thumb_cmd);
								cmd.poll_until_complete (500);
							}
							else if (__t__ (error)) {
								// pass;
							}
							else {
								print ('getting');
								if (__t__ (self.id !== null)) {
									self._thumbsize = size;
									self.thumbclient.call_func ('get_image', self._fetch_thumb, __kwargtrans__ ({item_ids: list ([self.id]), size: size, local: false, uri: true, item_type: self.item_type}));
								}
							}
						});},
						get _set_thumb_cmd () {return __get__ (this, function (self, cmd) {
							var val = cmd.get_value ();
							var im = null;
							if (__t__ (val)) {
								var im = val ['data'];
							}
							self._thumbs [self._thumbsize] = val;
							if (__t__ (!__t__ ((im)))) {
								var im = '/static/img/no-image.png';
							}
							self._set_thumb (im);
						});},
						get _set_thumb () {return __get__ (this, function (self, im) {
							if (self.get_node () && im) {
								self.node.find ('img').attr ('src', im);
								self.node.find ('.load').fadeOut (300);
							}
						});},
						get fetch_thumb () {return __get__ (this, function (self) {
							if (__t__ (!__t__ ((self.size_type)))) {
								return ;
							}
							var s = dict ({'big': 'Big', 'medium': 'Medium', 'small': 'Small'});
							var size = s [self.size_type];
							if (__t__ (self._thumbs [size])) {
								self._set_thumb (self._thumbs [size]);
							}
							else {
								self._fetch_thumb (__kwargtrans__ ({size: size}));
							}
						});}
					});
					var Gallery = __class__ ('Gallery', [Thumbnail], {
						get __init__ () {return __get__ (this, function (self, gtype, gallery_obj) {
							if (typeof gtype == 'undefined' || (gtype != null && gtype .hasOwnProperty ("__kwargtrans__"))) {;
								var gtype = 'medium';
							};
							if (typeof gallery_obj == 'undefined' || (gallery_obj != null && gallery_obj .hasOwnProperty ("__kwargtrans__"))) {;
								var gallery_obj = dict ({});
							};
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'gtype': var gtype = __allkwargs0__ [__attrib0__]; break;
											case 'gallery_obj': var gallery_obj = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
							}
							else {
							}
							self.obj = gallery_obj;
							var id = null;
							if (__in__ ('id', self.obj)) {
								var id = self.obj ['id'];
							}
							__super__ (Gallery, '__init__') (self, ('#gallery-' + gtype) + '-t', gtype, 'Gallery', id);
							self._gtype = gtype;
						});},
						get title () {return __get__ (this, function (self) {
							var t = '';
							if (__t__ (self.obj)) {
								if (__t__ (self.obj ['titles'])) {
									var t = self.obj ['titles'] [0] ['name'];
								}
							}
							return t;
						});},
						get titles () {return __get__ (this, function (self) {
							// pass;
							return a;
						});},
						get py_get () {return __get__ (this, function (self) {
							var g = dict ({});
							g ['id'] = self.obj ['id'];
							if (self._gtype == 'medium') {
								g ['title'] = self.title ();
								g ['thumb'] = 'static/img/default.png';
							}
							return g;
						});},
						get compile () {return __get__ (this, function (self, target_el, after, before, append, prepend) {
							if (typeof after == 'undefined' || (after != null && after .hasOwnProperty ("__kwargtrans__"))) {;
								var after = null;
							};
							if (typeof before == 'undefined' || (before != null && before .hasOwnProperty ("__kwargtrans__"))) {;
								var before = null;
							};
							if (typeof append == 'undefined' || (append != null && append .hasOwnProperty ("__kwargtrans__"))) {;
								var append = null;
							};
							if (typeof prepend == 'undefined' || (prepend != null && prepend .hasOwnProperty ("__kwargtrans__"))) {;
								var prepend = null;
							};
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'target_el': var target_el = __allkwargs0__ [__attrib0__]; break;
											case 'after': var after = __allkwargs0__ [__attrib0__]; break;
											case 'before': var before = __allkwargs0__ [__attrib0__]; break;
											case 'append': var append = __allkwargs0__ [__attrib0__]; break;
											case 'prepend': var prepend = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
							}
							else {
							}
							return __super__ (Gallery, 'compile') (self, target_el, __kwargtrans__ (__merge__ ({after: after, before: before, append: append, prepend: prepend}, self.py_get ())));
						});}
					});
					__pragma__ ('<use>' +
						'client' +
					'</use>')
					__pragma__ ('<all>')
						__all__.Base = Base;
						__all__.Command = Command;
						__all__.Gallery = Gallery;
						__all__.Thumbnail = Thumbnail;
						__all__.Widget = Widget;
						__all__.client = client;
						__all__.thumbclient = thumbclient;
					__pragma__ ('</all>')
				}
			}
		}
	);
