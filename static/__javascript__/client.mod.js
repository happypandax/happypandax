	__nest__ (
		__all__,
		'client', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var utils = {};
					__nest__ (utils, '', __init__ (__world__.utils));
					var debug = true;
					var Base = __class__ ('Base', [object], {
						get __init__ () {return __get__ (this, function (self, url) {
							if (typeof url == 'undefined' || (url != null && url .hasOwnProperty ("__kwargtrans__"))) {;
								var url = '';
							};
							self.url = utils.URLManipulator (url);
							self._flashes = list ([]);
						});},
						get main () {return __get__ (this, function (self) {
							if (self.url) {
								self.log ('setting active menu item');
								var each_d = function (index) {
									var aurl = $ (this).find ('a').attr ('href');
									if (aurl == self.url.path ()) {
										$ (this).addClass ('active');
										$ (this).find ('a').append ('<span class="sr-only">(current)</span>');
									}
								};
								$ ('#nav-collapse li').each (each_d);
							}
						});},
						get log () {return __get__ (this, function (self, msg) {
							if (debug) {
								print (msg);
							}
						});},
						get flash () {return __get__ (this, function (self, msg, flash_type, strong) {
							if (typeof flash_type == 'undefined' || (flash_type != null && flash_type .hasOwnProperty ("__kwargtrans__"))) {;
								var flash_type = 'danger';
							};
							if (typeof strong == 'undefined' || (strong != null && strong .hasOwnProperty ("__kwargtrans__"))) {;
								var strong = '';
							};
							var lbl = 'alert-' + flash_type;
							var obj = self.compile ('#global-flash-t', '#global-flash', __kwargtrans__ ({prepend: true, alert: lbl, strong: strong, msg: msg}));
							obj.delay (8000).fadeOut (500);
						});},
						get get_label () {return __get__ (this, function (self, label_type) {
							return 'label-' + label_type;
						});},
						get compile () {return __get__ (this, function (self, source_el, target_el, after, before, append, prepend) {
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
											case 'source_el': var source_el = __allkwargs0__ [__attrib0__]; break;
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
							var src = $ (source_el).html ();
							if (!(src)) {
								console.error ('{} could not be found, compilation aborted'.format (source_el));
								return ;
							}
							var tmpl = Handlebars.compile (src);
							if (after) {
								return $ (tmpl (data)).insertAfter (target_el);
							}
							else if (before) {
								return $ (tmpl (data)).insertBefore (target_el);
							}
							else if (append) {
								return $ (tmpl (data)).appendTo (target_el);
							}
							else if (prepend) {
								return $ (tmpl (data)).prependTo (target_el);
							}
							else {
								return $ (target_el).html (tmpl (data));
							}
						});},
						get flash_error () {return __get__ (this, function (self, error, flash_type) {
							if (typeof flash_type == 'undefined' || (flash_type != null && flash_type .hasOwnProperty ("__kwargtrans__"))) {;
								var flash_type = 'danger';
							};
							if (error) {
								self.flash (error ['msg'], flash_type, error ['code']);
							}
						});}
					});
					var ServerMsg = __class__ ('ServerMsg', [object], {
						msg_id: 0,
						get __init__ () {return __get__ (this, function (self, data, callback, func_name) {
							if (typeof callback == 'undefined' || (callback != null && callback .hasOwnProperty ("__kwargtrans__"))) {;
								var callback = null;
							};
							if (typeof func_name == 'undefined' || (func_name != null && func_name .hasOwnProperty ("__kwargtrans__"))) {;
								var func_name = null;
							};
							ServerMsg.msg_id++;
							self.id = self.msg_id;
							self.data = data;
							self.callback = callback;
							self.func_name = func_name;
						});}
					});
					var Client = __class__ ('Client', [Base], {
						polling: false,
						get __init__ () {return __get__ (this, function (self, session, namespace, py_new) {
							if (typeof session == 'undefined' || (session != null && session .hasOwnProperty ("__kwargtrans__"))) {;
								var session = '';
							};
							if (typeof namespace == 'undefined' || (namespace != null && namespace .hasOwnProperty ("__kwargtrans__"))) {;
								var namespace = '';
							};
							if (typeof py_new == 'undefined' || (py_new != null && py_new .hasOwnProperty ("__kwargtrans__"))) {;
								var py_new = false;
							};
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'session': var session = __allkwargs0__ [__attrib0__]; break;
											case 'namespace': var namespace = __allkwargs0__ [__attrib0__]; break;
											case 'py_new': var py_new = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
							}
							else {
							}
							self.socket_url = ((((location.protocol + '//') + location.hostname) + ':') + location.port) + namespace;
							self.socket = io (self.socket_url, dict ({'forceNew': py_new, 'transports': list (['websocket'])}));
							self.socket.on ('command', self.on_command);
							self.socket.on ('server_call', self.on_server_call);
							self.socket.on ('exception', self.on_error);
							self.commands = dict ({'connect': 1, 'reconnect': 2, 'disconnect': 3, 'status': 4, 'handshake': 5});
							self.namespace = namespace;
							self.session = session;
							self.py_name = 'webclient';
							self._connection_status = true;
							self._disconnected_once = false;
							self._response_cb = dict ({});
							self._last_msg = null;
							self._msg_queue = list ([]);
							self._cmd_status = dict ({});
							self._cmd_status_c = 0;
							if (!(self.polling)) {
								utils.poll_func (self.connection, 3000000, 15000);
								Client.polling = true;
							}
						});},
						get connection () {return __get__ (this, function (self) {
							self.send_command (self.commands ['status']);
							if (!(self._connection_status)) {
								self.flash ('Trying to establish server connection...', 'info');
								self.send_command (self.commands ['connect']);
							}
							return false;
						});},
						get send_command () {return __get__ (this, function (self, cmd) {
							self.socket.emit ('command', dict ({'command': cmd}));
						});},
						get on_command () {return __get__ (this, function (self, msg) {
							self._connection_status = msg ['status'];
							var st_txt = 'unknown';
							var st_label = self.get_label ('default');
							if (self._connection_status) {
								if (self._disconnected_once) {
									self._disconnected_once = false;
									self.flash ('Connection to server has been established', 'success');
								}
								var st_txt = 'connected';
								var st_label = self.get_label ('success');
							}
							else {
								self._disconnected_once = true;
								var st_txt = 'disconnected';
								var st_label = self.get_label ('danger');
							}
							self.compile ('#server-status-t', '#server-status', __kwargtrans__ (dict ({'status': st_txt, 'label': st_label})));
						});},
						get on_error () {return __get__ (this, function (self, msg) {
							self.flash (msg ['error'], 'danger');
						});},
						get on_server_call () {return __get__ (this, function (self, msg) {
							if (__t__ (self._response_cb)) {
								var serv_msg = self._response_cb.py_pop (msg ['id']);
								var serv_data = msg ['msg'];
								self.session = serv_data ['session'];
								if (__t__ (__in__ ('error', serv_data))) {
									self.flash_error (serv_data ['error']);
									if (__t__ (serv_data ['error'] ['code'] == 408)) {
										self.send_command (self.commands ['handshake']);
									}
								}
								if (__t__ (__t__ (serv_msg.func_name) && serv_data)) {
									for (var func of __i__ (serv_data.data)) {
										var err = null;
										if (__t__ (__in__ ('error', func))) {
											var err = func ['error'];
											self.flash_error (err);
										}
										if (__t__ (func ['fname'] == serv_msg.func_name)) {
											if (__t__ (serv_msg.callback)) {
												serv_msg.callback (func ['data'], err);
											}
											break;
										}
									}
								}
								else if (__t__ (serv_msg.callback)) {
									serv_msg.callback (serv_data);
								}
							}
						});},
						get call_func () {return __get__ (this, function (self, func_name, callback) {
							var kwargs = dict ();
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'func_name': var func_name = __allkwargs0__ [__attrib0__]; break;
											case 'callback': var callback = __allkwargs0__ [__attrib0__]; break;
											default: kwargs [__attrib0__] = __allkwargs0__ [__attrib0__];
										}
									}
									delete kwargs.__kwargtrans__;
								}
							}
							else {
							}
							var f_dict = dict ({'fname': func_name});
							f_dict.py_update (kwargs);
							self.call (ServerMsg (list ([f_dict]), callback, func_name));
						});},
						get call () {return __get__ (this, function (self, servermsg) {
							self._response_cb [servermsg.id] = servermsg;
							var final_msg = dict ({'id': servermsg.id, 'msg': dict ({'session': self.session, 'name': self.py_name, 'data': servermsg.data})});
							self._last_msg = final_msg;
							if (self._connection_status) {
								self.socket.emit ('server_call', final_msg);
							}
							else {
								self._msg_queue.append (final_msg);
							}
						});}
					});
					var client = Client ();
					var thumbclient = Client (__kwargtrans__ ({namespace: '/thumb', py_new: true}));
					var commandclient = Client (__kwargtrans__ ({namespace: '/command', py_new: true}));
					var Command = __class__ ('Command', [Base], {
						get __init__ () {return __get__ (this, function (self, command_ids, customclient) {
							if (typeof customclient == 'undefined' || (customclient != null && customclient .hasOwnProperty ("__kwargtrans__"))) {;
								var customclient = null;
							};
							__super__ (Command, '__init__') (self);
							self._single_id = null;
							if (isinstance (command_ids, int)) {
								self._single_id = command_ids;
								var command_ids = list ([command_ids]);
							}
							self._command_ids = command_ids;
							self._states = dict ({});
							self._values = dict ({});
							self._value_callback = null;
							self._getting_value = false;
							self.commandclient = commandclient;
							for (var i of self._command_ids) {
								self._states [str (i)] = null;
								self._values [str (i)] = null;
							}
							if (customclient) {
								self.commandclient = customclient;
							}
						});},
						get _check_status () {return __get__ (this, function (self, data, error) {
							if (typeof data == 'undefined' || (data != null && data .hasOwnProperty ("__kwargtrans__"))) {;
								var data = null;
							};
							if (typeof error == 'undefined' || (error != null && error .hasOwnProperty ("__kwargtrans__"))) {;
								var error = null;
							};
							if (data !== null && !(error)) {
								var states = list ([]);
								for (var i of __i__ (self._command_ids)) {
									var str_i = str (i);
									self._states [str_i] = data [str_i];
								}
							}
							else if (error) {
								// pass;
							}
							else {
								self.commandclient.call_func ('get_command_state', self._check_status, __kwargtrans__ ({command_ids: self._command_ids}));
							}
						});},
						get finished () {return __get__ (this, function (self) {
							var states = list ([]);
							for (var s of __i__ (self._states)) {
								states.append (__in__ (self._states [s], list (['finished', 'stopped', 'failed'])));
							}
							return all (states);
						});},
						get poll_until_complete () {return __get__ (this, function (self, interval, timeout, callback) {
							if (typeof interval == 'undefined' || (interval != null && interval .hasOwnProperty ("__kwargtrans__"))) {;
								var interval = 1000 * 5;
							};
							if (typeof timeout == 'undefined' || (timeout != null && timeout .hasOwnProperty ("__kwargtrans__"))) {;
								var timeout = (1000 * 60) * 10;
							};
							if (typeof callback == 'undefined' || (callback != null && callback .hasOwnProperty ("__kwargtrans__"))) {;
								var callback = null;
							};
							if (!(self.finished ())) {
								var _poll = function () {
									if (!(self.finished ())) {
										self._check_status ();
									}
									else {
										self._fetch_value ();
										if (callback) {
											callback ();
										}
									}
									return self.finished ();
								};
								utils.poll_func (_poll, timeout, interval);
							}
						});},
						get _fetch_value () {return __get__ (this, function (self, data, error, cmd_ids) {
							if (typeof data == 'undefined' || (data != null && data .hasOwnProperty ("__kwargtrans__"))) {;
								var data = null;
							};
							if (typeof error == 'undefined' || (error != null && error .hasOwnProperty ("__kwargtrans__"))) {;
								var error = null;
							};
							if (typeof cmd_ids == 'undefined' || (cmd_ids != null && cmd_ids .hasOwnProperty ("__kwargtrans__"))) {;
								var cmd_ids = null;
							};
							if (data !== null && !(error)) {
								for (var i of __i__ (self._command_ids)) {
									var str_i = str (i);
									if (__in__ (str_i, data)) {
										self._values [str_i] = data [str_i];
									}
								}
								if (self._value_callback) {
									self._value_callback (self);
								}
								self._getting_value = false;
							}
							else if (error) {
								// pass;
							}
							else if (!(self._getting_value)) {
								if (!(cmd_ids)) {
									var cmd_ids = self._command_ids;
								}
								self.commandclient.call_func ('get_command_value', self._fetch_value, __kwargtrans__ ({command_ids: cmd_ids}));
								self._getting_value = true;
							}
						});},
						get get_value () {return __get__ (this, function (self, cmd_id) {
							if (typeof cmd_id == 'undefined' || (cmd_id != null && cmd_id .hasOwnProperty ("__kwargtrans__"))) {;
								var cmd_id = null;
							};
							if (__t__ (__t__ (cmd_id) && !__t__ ((isinstance (cmd_id, list))))) {
								var cmd_id = list ([str (cmd_id)]);
							}
							if (__t__ (!__t__ ((cmd_id)))) {
								var cmd_id = self._command_ids;
							}
							var ids = list ([]);
							for (var i of __i__ (cmd_id)) {
								if (__t__ (!__t__ ((self._values [i])))) {
									ids.append (int (i));
								}
							}
							if (__t__ (ids)) {
								self._fetch_value (__kwargtrans__ ({cmd_ids: ids}));
							}
							if (__t__ (self._single_id)) {
								return self._values [str (self._single_id)];
							}
							return self._values;
						});},
						get set_callback () {return __get__ (this, function (self, callback) {
							self._value_callback = callback;
						});}
					});
					__pragma__ ('<use>' +
						'utils' +
					'</use>')
					__pragma__ ('<all>')
						__all__.Base = Base;
						__all__.Client = Client;
						__all__.Command = Command;
						__all__.ServerMsg = ServerMsg;
						__all__.client = client;
						__all__.commandclient = commandclient;
						__all__.debug = debug;
						__all__.thumbclient = thumbclient;
					__pragma__ ('</all>')
				}
			}
		}
	);
