	__nest__ (
		__all__,
		'utils', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var syntax_highlight = 
					    function syntax_highlight(json) {
					        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
					        return json.replace(/("(\u[a-zA-Z0-9]{4}|\[^u]|[^\"])*"(\s*:)?|(true|false|null)|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, function (match) {
					            var cls = 'json-number';
					            if (/^"/.test(match)) {
					                if (/:$/.test(match)) {
					                    cls = 'json-key';
					                } else {
					                    cls = 'json-string';
					                }
					            } else if (/true|false/.test(match)) {
					                cls = 'json-boolean';
					            } else if (/null/.test(match)) {
					                cls = 'json-null';
					            }
					            return '<span class="' + cls + '">' + match + '</span>';
					        });
					    }
					var poll_func = 
					    function poll_func(fn, timeout, interval) {
					    var startTime = (new Date()).getTime();
					    interval = interval || 1000;
					    var canPoll = true;
					
					    (function p() {
					        canPoll = ((new Date).getTime() - startTime ) <= timeout;
					        if (!fn() && canPoll)  { // ensures the function exucutes
					            setTimeout(p, interval);
					        }
					    })();
					    }
					var html_escape_table = dict ({'&': '&amp;', '"': '&quot;', "'": '&apos;', '>': '&gt;', '<': '&lt;'});
					var html_escape = function (text) {
						return ''.join (function () {
							var __accu0__ = [];
							for (var c of text) {
								__accu0__.append (html_escape_table.py_get (c, c));
							}
							return py_iter (__accu0__);
						} ());
					};
					var get_locale = function () {
						return window.navigator.userLanguage || window.navigator.language;
					};
					var Grid = __class__ ('Grid', [object], {
						get __init__ () {return __get__ (this, function (self, container_el, child_el) {
							var kwargs = dict ();
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'container_el': var container_el = __allkwargs0__ [__attrib0__]; break;
											case 'child_el': var child_el = __allkwargs0__ [__attrib0__]; break;
											default: kwargs [__attrib0__] = __allkwargs0__ [__attrib0__];
										}
									}
									delete kwargs.__kwargtrans__;
								}
							}
							else {
							}
							self._grid = $ (container_el);
							self._options = dict ({'itemSelector': child_el});
							self._options.py_update (kwargs);
							self._grid.packery (self._options);
						});},
						get reload () {return __get__ (this, function (self) {
							self._grid.packery ('reloadItems');
						});},
						get layout () {return __get__ (this, function (self) {
							self._grid.packery ();
						});}
					});
					var URLManipulator = __class__ ('URLManipulator', [object], {
						get __init__ () {return __get__ (this, function (self, url) {
							if (typeof url == 'undefined' || (url != null && url .hasOwnProperty ("__kwargtrans__"))) {;
								var url = null;
							};
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'url': var url = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
							}
							else {
							}
							if (url) {
								self.uri = URI (url);
							}
							else {
								self.uri = URI ();
							}
						});},
						get path () {return __get__ (this, function (self) {
							return self.uri.pathname ();
						});},
						get go () {return __get__ (this, function (self, url) {
							history.pushState (null, null, url);
						});}
					});
					__pragma__ ('<all>')
						__all__.Grid = Grid;
						__all__.URLManipulator = URLManipulator;
						__all__.get_locale = get_locale;
						__all__.html_escape = html_escape;
						__all__.html_escape_table = html_escape_table;
						__all__.poll_func = poll_func;
						__all__.syntax_highlight = syntax_highlight;
					__pragma__ ('</all>')
				}
			}
		}
	);
