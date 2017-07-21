	__nest__ (
		__all__,
		'gallery', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var client = __init__ (__world__.client).client;
					var Base = __init__ (__world__.client).Base;
					var Command = __init__ (__world__.client).Command;
					var Gallery = __class__ ('Gallery', [Base], {
						get __init__ () {return __get__ (this, function (self, gtype, gallery_obj, url) {
							if (typeof gtype == 'undefined' || (gtype != null && gtype .hasOwnProperty ("__kwargtrans__"))) {;
								var gtype = 'medium';
							};
							if (typeof gallery_obj == 'undefined' || (gallery_obj != null && gallery_obj .hasOwnProperty ("__kwargtrans__"))) {;
								var gallery_obj = dict ({});
							};
							if (typeof url == 'undefined' || (url != null && url .hasOwnProperty ("__kwargtrans__"))) {;
								var url = '';
							};
							__super__ (Gallery, '__init__') (self, url);
							self._gtype = gtype;
							self.obj = gallery_obj;
							self._node = null;
							self._thumbs = dict ({'Big': null, 'Medium': null, 'Small': null});
							self._thumbsize = null;
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
								var cmd_id = data [str (self.obj ['id'])];
								var cmd = Command (cmd_id);
								self._thumbs [self._thumbsize] = cmd;
								cmd.set_callback (self._set_thumb);
								cmd.poll_until_complete (1000);
							}
							else if (__t__ (error)) {
								// pass;
							}
							else if (__t__ (self.obj)) {
								self._thumbsize = size;
								client.call_func ('get_cover', self._fetch_thumb, __kwargtrans__ ({item_ids: list ([self.obj ['id']]), size: size, local: false, uri: true, item_type: 'Gallery'}));
							}
						});},
						get _set_thumb () {return __get__ (this, function (self, cmd) {
							var val = cmd.get_value ();
							self._thumbs [self._thumbsize] = val;
							var im = 'static/img/no-image.png';
							if (__t__ (val)) {
								var im = val ['data'];
							}
							if (__t__ (self._node)) {
								self._node.find ('img').attr ('src', im);
								self._node.find ('.load').fadeOut (300);
							}
						});},
						get fetch_thumb () {return __get__ (this, function (self) {
							if (__t__ (!__t__ ((self._gtype)))) {
								return ;
							}
							var s = dict ({'medium': 'Medium', 'small': 'Small'});
							var size = s [self._gtype];
							if (__t__ (!__t__ ((self._thumbs [size])))) {
								self._fetch_thumb (__kwargtrans__ ({size: size}));
							}
						});},
						get link_node () {return __get__ (this, function (self, py_selector) {
							if (typeof py_selector == 'undefined' || (py_selector != null && py_selector .hasOwnProperty ("__kwargtrans__"))) {;
								var py_selector = null;
							};
							if (!(py_selector) && !(self.obj)) {
								return ;
							}
							if (!(py_selector)) {
								var py_selector = '#g-{}-{}'.format (self._gtype, self.obj ['id']);
							}
							self._node = $ (py_selector);
						});},
						get py_get () {return __get__ (this, function (self) {
							var g = dict ({});
							g ['id'] = self.obj ['id'];
							if (self._gtype == 'medium') {
								g ['title'] = self.title ();
								g ['thumb'] = 'static/img/default.png';
							}
							return g;
						});}
					});
					__pragma__ ('<use>' +
						'client' +
					'</use>')
					__pragma__ ('<all>')
						__all__.Base = Base;
						__all__.Command = Command;
						__all__.Gallery = Gallery;
						__all__.client = client;
					__pragma__ ('</all>')
				}
			}
		}
	);
