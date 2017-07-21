"use strict";
// Transcrypt'ed from Python, 2017-07-21 01:58:20
function pages () {
   var __symbols__ = ['__py3.5__', '__esv6__'];
    var __all__ = {};
    var __world__ = __all__;
    
    // Nested object creator, part of the nesting may already exist and have attributes
    var __nest__ = function (headObject, tailNames, value) {
        // In some cases this will be a global object, e.g. 'window'
        var current = headObject;
        
        if (tailNames != '') {  // Split on empty string doesn't give empty list
            // Find the last already created object in tailNames
            var tailChain = tailNames.split ('.');
            var firstNewIndex = tailChain.length;
            for (var index = 0; index < tailChain.length; index++) {
                if (!current.hasOwnProperty (tailChain [index])) {
                    firstNewIndex = index;
                    break;
                }
                current = current [tailChain [index]];
            }
            
            // Create the rest of the objects, if any
            for (var index = firstNewIndex; index < tailChain.length; index++) {
                current [tailChain [index]] = {};
                current = current [tailChain [index]];
            }
        }
        
        // Insert it new attributes, it may have been created earlier and have other attributes
        for (var attrib in value) {
            current [attrib] = value [attrib];          
        }       
    };
    __all__.__nest__ = __nest__;
    
    // Initialize module if not yet done and return its globals
    var __init__ = function (module) {
        if (!module.__inited__) {
            module.__all__.__init__ (module.__all__);
            module.__inited__ = true;
        }
        return module.__all__;
    };
    __all__.__init__ = __init__;
    
    
    // Proxy switch, controlled by __pragma__ ('proxy') and __pragma ('noproxy')
    var __proxy__ = false;  // No use assigning it to __all__, only its transient state is important
    
    
    // Since we want to assign functions, a = b.f should make b.f produce a bound function
    // So __get__ should be called by a property rather then a function
    // Factory __get__ creates one of three curried functions for func
    // Which one is produced depends on what's to the left of the dot of the corresponding JavaScript property
    var __get__ = function (self, func, quotedFuncName) {
        if (self) {
            if (self.hasOwnProperty ('__class__') || typeof self == 'string' || self instanceof String) {           // Object before the dot
                if (quotedFuncName) {                                   // Memoize call since fcall is on, by installing bound function in instance
                    Object.defineProperty (self, quotedFuncName, {      // Will override the non-own property, next time it will be called directly
                        value: function () {                            // So next time just call curry function that calls function
                            var args = [] .slice.apply (arguments);
                            return func.apply (null, [self] .concat (args));
                        },              
                        writable: true,
                        enumerable: true,
                        configurable: true
                    });
                }
                return function () {                                    // Return bound function, code dupplication for efficiency if no memoizing
                    var args = [] .slice.apply (arguments);             // So multilayer search prototype, apply __get__, call curry func that calls func
                    return func.apply (null, [self] .concat (args));
                };
            }
            else {                                                      // Class before the dot
                return func;                                            // Return static method
            }
        }
        else {                                                          // Nothing before the dot
            return func;                                                // Return free function
        }
    }
    __all__.__get__ = __get__;
        
    // Mother of all metaclasses        
    var py_metatype = {
        __name__: 'type',
        __bases__: [],
        
        // Overridable class creation worker
        __new__: function (meta, name, bases, attribs) {
            // Create the class cls, a functor, which the class creator function will return
            var cls = function () {                     // If cls is called with arg0, arg1, etc, it calls its __new__ method with [arg0, arg1, etc]
                var args = [] .slice.apply (arguments); // It has a __new__ method, not yet but at call time, since it is copied from the parent in the loop below
                return cls.__new__ (args);              // Each Python class directly or indirectly derives from object, which has the __new__ method
            };                                          // If there are no bases in the Python source, the compiler generates [object] for this parameter
            
            // Copy all methods, including __new__, properties and static attributes from base classes to new cls object
            // The new class object will simply be the prototype of its instances
            // JavaScript prototypical single inheritance will do here, since any object has only one class
            // This has nothing to do with Python multiple inheritance, that is implemented explictly in the copy loop below
            for (var index = bases.length - 1; index >= 0; index--) {   // Reversed order, since class vars of first base should win
                var base = bases [index];
                for (var attrib in base) {
                    var descrip = Object.getOwnPropertyDescriptor (base, attrib);
                    Object.defineProperty (cls, attrib, descrip);
                }           

                for (var symbol of Object.getOwnPropertySymbols (base)) {
                    var descrip = Object.getOwnPropertyDescriptor (base, symbol);
                    Object.defineProperty (cls, symbol, descrip);
                }
                
            }
            
            // Add class specific attributes to the created cls object
            cls.__metaclass__ = meta;
            cls.__name__ = name;
            cls.__bases__ = bases;
            
            // Add own methods, properties and own static attributes to the created cls object
            for (var attrib in attribs) {
                var descrip = Object.getOwnPropertyDescriptor (attribs, attrib);
                Object.defineProperty (cls, attrib, descrip);
            }

            for (var symbol of Object.getOwnPropertySymbols (attribs)) {
                var descrip = Object.getOwnPropertyDescriptor (attribs, symbol);
                Object.defineProperty (cls, symbol, descrip);
            }
            
            // Return created cls object
            return cls;
        }
    };
    py_metatype.__metaclass__ = py_metatype;
    __all__.py_metatype = py_metatype;
    
    // Mother of all classes
    var object = {
        __init__: function (self) {},
        
        __metaclass__: py_metatype, // By default, all classes have metaclass type, since they derive from object
        __name__: 'object',
        __bases__: [],
            
        // Object creator function, is inherited by all classes (so could be global)
        __new__: function (args) {  // Args are just the constructor args       
            // In JavaScript the Python class is the prototype of the Python object
            // In this way methods and static attributes will be available both with a class and an object before the dot
            // The descriptor produced by __get__ will return the right method flavor
            var instance = Object.create (this, {__class__: {value: this, enumerable: true}});
            
            if ('__getattr__' in this || '__setattr__' in this) {
                instance = new Proxy (instance, {
                    get: function (target, name) {
                        var result = target [name];
                        if (result == undefined) {  // Target doesn't have attribute named name
                            return target.__getattr__ (name);
                        }
                        else {
                            return result;
                        }
                    },
                    set: function (target, name, value) {
                        try {
                            target.__setattr__ (name, value);
                        }
                        catch (exception) {         // Target doesn't have a __setattr__ method
                            target [name] = value;
                        }
                        return true;
                    }
                })
            }

            // Call constructor
            this.__init__.apply (null, [instance] .concat (args));

            // Return constructed instance
            return instance;
        }   
    };
    __all__.object = object;
    
    // Class creator facade function, calls class creation worker
    var __class__ = function (name, bases, attribs, meta) {         // Parameter meta is optional
        if (meta == undefined) {
            meta = bases [0] .__metaclass__;
        }
                
        return meta.__new__ (meta, name, bases, attribs);
    }
    __all__.__class__ = __class__;
    
    // Define __pragma__ to preserve '<all>' and '</all>', since it's never generated as a function, must be done early, so here
    var __pragma__ = function () {};
    __all__.__pragma__ = __pragma__;
    
    	__nest__ (
		__all__,
		'org.transcrypt.__base__', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var __Envir__ = __class__ ('__Envir__', [object], {
						get __init__ () {return __get__ (this, function (self) {
							self.interpreter_name = 'python';
							self.transpiler_name = 'transcrypt';
							self.transpiler_version = '3.6.27';
							self.target_subdir = '__javascript__';
						});}
					});
					var __envir__ = __Envir__ ();
					__pragma__ ('<all>')
						__all__.__Envir__ = __Envir__;
						__all__.__envir__ = __envir__;
					__pragma__ ('</all>')
				}
			}
		}
	);
	__nest__ (
		__all__,
		'org.transcrypt.__standard__', {
			__all__: {
				__inited__: false,
				__init__: function (__all__) {
					var Exception = __class__ ('Exception', [object], {
						get __init__ () {return __get__ (this, function (self) {
							var kwargs = dict ();
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											default: kwargs [__attrib0__] = __allkwargs0__ [__attrib0__];
										}
									}
									delete kwargs.__kwargtrans__;
								}
								var args = tuple ([].slice.apply (arguments).slice (1, __ilastarg0__ + 1));
							}
							else {
								var args = tuple ();
							}
							self.__args__ = args;
							try {
								self.stack = kwargs.error.stack;
							}
							catch (__except0__) {
								self.stack = 'No stack trace available';
							}
						});},
						get __repr__ () {return __get__ (this, function (self) {
							if (len (self.__args__)) {
								return '{}{}'.format (self.__class__.__name__, repr (tuple (self.__args__)));
							}
							else {
								return '{}()'.format (self.__class__.__name__);
							}
						});},
						get __str__ () {return __get__ (this, function (self) {
							if (len (self.__args__) > 1) {
								return str (tuple (self.__args__));
							}
							else if (len (self.__args__)) {
								return str (self.__args__ [0]);
							}
							else {
								return '';
							}
						});}
					});
					var IterableError = __class__ ('IterableError', [Exception], {
						get __init__ () {return __get__ (this, function (self, error) {
							Exception.__init__ (self, "Can't iterate over non-iterable", __kwargtrans__ ({error: error}));
						});}
					});
					var StopIteration = __class__ ('StopIteration', [Exception], {
						get __init__ () {return __get__ (this, function (self, error) {
							Exception.__init__ (self, 'Iterator exhausted', __kwargtrans__ ({error: error}));
						});}
					});
					var ValueError = __class__ ('ValueError', [Exception], {
						get __init__ () {return __get__ (this, function (self, error) {
							Exception.__init__ (self, 'Erroneous value', __kwargtrans__ ({error: error}));
						});}
					});
					var KeyError = __class__ ('KeyError', [Exception], {
						get __init__ () {return __get__ (this, function (self, error) {
							Exception.__init__ (self, 'Invalid key', __kwargtrans__ ({error: error}));
						});}
					});
					var AssertionError = __class__ ('AssertionError', [Exception], {
						get __init__ () {return __get__ (this, function (self, message, error) {
							if (message) {
								Exception.__init__ (self, message, __kwargtrans__ ({error: error}));
							}
							else {
								Exception.__init__ (self, __kwargtrans__ ({error: error}));
							}
						});}
					});
					var NotImplementedError = __class__ ('NotImplementedError', [Exception], {
						get __init__ () {return __get__ (this, function (self, message, error) {
							Exception.__init__ (self, message, __kwargtrans__ ({error: error}));
						});}
					});
					var IndexError = __class__ ('IndexError', [Exception], {
						get __init__ () {return __get__ (this, function (self, message, error) {
							Exception.__init__ (self, message, __kwargtrans__ ({error: error}));
						});}
					});
					var AttributeError = __class__ ('AttributeError', [Exception], {
						get __init__ () {return __get__ (this, function (self, message, error) {
							Exception.__init__ (self, message, __kwargtrans__ ({error: error}));
						});}
					});
					var Warning = __class__ ('Warning', [Exception], {
					});
					var UserWarning = __class__ ('UserWarning', [Warning], {
					});
					var DeprecationWarning = __class__ ('DeprecationWarning', [Warning], {
					});
					var RuntimeWarning = __class__ ('RuntimeWarning', [Warning], {
					});
					var __sort__ = function (iterable, key, reverse) {
						if (typeof key == 'undefined' || (key != null && key .hasOwnProperty ("__kwargtrans__"))) {;
							var key = null;
						};
						if (typeof reverse == 'undefined' || (reverse != null && reverse .hasOwnProperty ("__kwargtrans__"))) {;
							var reverse = false;
						};
						if (arguments.length) {
							var __ilastarg0__ = arguments.length - 1;
							if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
								var __allkwargs0__ = arguments [__ilastarg0__--];
								for (var __attrib0__ in __allkwargs0__) {
									switch (__attrib0__) {
										case 'iterable': var iterable = __allkwargs0__ [__attrib0__]; break;
										case 'key': var key = __allkwargs0__ [__attrib0__]; break;
										case 'reverse': var reverse = __allkwargs0__ [__attrib0__]; break;
									}
								}
							}
						}
						else {
						}
						if (key) {
							iterable.sort ((function __lambda__ (a, b) {
								if (arguments.length) {
									var __ilastarg0__ = arguments.length - 1;
									if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
										var __allkwargs0__ = arguments [__ilastarg0__--];
										for (var __attrib0__ in __allkwargs0__) {
											switch (__attrib0__) {
												case 'a': var a = __allkwargs0__ [__attrib0__]; break;
												case 'b': var b = __allkwargs0__ [__attrib0__]; break;
											}
										}
									}
								}
								else {
								}
								return (key (a) > key (b) ? 1 : -(1));
							}));
						}
						else {
							iterable.sort ();
						}
						if (reverse) {
							iterable.reverse ();
						}
					};
					var sorted = function (iterable, key, reverse) {
						if (typeof key == 'undefined' || (key != null && key .hasOwnProperty ("__kwargtrans__"))) {;
							var key = null;
						};
						if (typeof reverse == 'undefined' || (reverse != null && reverse .hasOwnProperty ("__kwargtrans__"))) {;
							var reverse = false;
						};
						if (arguments.length) {
							var __ilastarg0__ = arguments.length - 1;
							if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
								var __allkwargs0__ = arguments [__ilastarg0__--];
								for (var __attrib0__ in __allkwargs0__) {
									switch (__attrib0__) {
										case 'iterable': var iterable = __allkwargs0__ [__attrib0__]; break;
										case 'key': var key = __allkwargs0__ [__attrib0__]; break;
										case 'reverse': var reverse = __allkwargs0__ [__attrib0__]; break;
									}
								}
							}
						}
						else {
						}
						if (py_typeof (iterable) == dict) {
							var result = copy (iterable.py_keys ());
						}
						else {
							var result = copy (iterable);
						}
						__sort__ (result, key, reverse);
						return result;
					};
					var map = function (func, iterable) {
						return function () {
							var __accu0__ = [];
							for (var item of iterable) {
								__accu0__.append (func (item));
							}
							return __accu0__;
						} ();
					};
					var filter = function (func, iterable) {
						if (func == null) {
							var func = bool;
						}
						return function () {
							var __accu0__ = [];
							for (var item of iterable) {
								if (func (item)) {
									__accu0__.append (item);
								}
							}
							return __accu0__;
						} ();
					};
					var __Terminal__ = __class__ ('__Terminal__', [object], {
						get __init__ () {return __get__ (this, function (self) {
							self.buffer = '';
							try {
								self.element = document.getElementById ('__terminal__');
							}
							catch (__except0__) {
								self.element = null;
							}
							if (self.element) {
								self.element.style.overflowX = 'auto';
								self.element.style.boxSizing = 'border-box';
								self.element.style.padding = '5px';
								self.element.innerHTML = '_';
							}
						});},
						get print () {return __get__ (this, function (self) {
							var sep = ' ';
							var end = '\n';
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'sep': var sep = __allkwargs0__ [__attrib0__]; break;
											case 'end': var end = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
								var args = tuple ([].slice.apply (arguments).slice (1, __ilastarg0__ + 1));
							}
							else {
								var args = tuple ();
							}
							self.buffer = '{}{}{}'.format (self.buffer, sep.join (function () {
								var __accu0__ = [];
								for (var arg of args) {
									__accu0__.append (str (arg));
								}
								return __accu0__;
							} ()), end).__getslice__ (-(4096), null, 1);
							if (self.element) {
								self.element.innerHTML = self.buffer.py_replace ('\n', '<br>');
								self.element.scrollTop = self.element.scrollHeight;
							}
							else {
								console.log (sep.join (function () {
									var __accu0__ = [];
									for (var arg of args) {
										__accu0__.append (str (arg));
									}
									return __accu0__;
								} ()));
							}
						});},
						get input () {return __get__ (this, function (self, question) {
							if (arguments.length) {
								var __ilastarg0__ = arguments.length - 1;
								if (arguments [__ilastarg0__] && arguments [__ilastarg0__].hasOwnProperty ("__kwargtrans__")) {
									var __allkwargs0__ = arguments [__ilastarg0__--];
									for (var __attrib0__ in __allkwargs0__) {
										switch (__attrib0__) {
											case 'self': var self = __allkwargs0__ [__attrib0__]; break;
											case 'question': var question = __allkwargs0__ [__attrib0__]; break;
										}
									}
								}
							}
							else {
							}
							self.print ('{}'.format (question), __kwargtrans__ ({end: ''}));
							var answer = window.prompt ('\n'.join (self.buffer.py_split ('\n').__getslice__ (-(16), null, 1)));
							self.print (answer);
							return answer;
						});}
					});
					var __terminal__ = __Terminal__ ();
					__pragma__ ('<all>')
						__all__.AssertionError = AssertionError;
						__all__.AttributeError = AttributeError;
						__all__.DeprecationWarning = DeprecationWarning;
						__all__.Exception = Exception;
						__all__.IndexError = IndexError;
						__all__.IterableError = IterableError;
						__all__.KeyError = KeyError;
						__all__.NotImplementedError = NotImplementedError;
						__all__.RuntimeWarning = RuntimeWarning;
						__all__.StopIteration = StopIteration;
						__all__.UserWarning = UserWarning;
						__all__.ValueError = ValueError;
						__all__.Warning = Warning;
						__all__.__Terminal__ = __Terminal__;
						__all__.__sort__ = __sort__;
						__all__.__terminal__ = __terminal__;
						__all__.filter = filter;
						__all__.map = map;
						__all__.sorted = sorted;
					__pragma__ ('</all>')
				}
			}
		}
	);
    var __call__ = function (/* <callee>, <this>, <params>* */) {   // Needed for __base__ and __standard__ if global 'opov' switch is on
        var args = [] .slice.apply (arguments);
        if (typeof args [0] == 'object' && '__call__' in args [0]) {        // Overloaded
            return args [0] .__call__ .apply (args [1], args.slice (2));
        }
        else {                                                              // Native
            return args [0] .apply (args [1], args.slice (2));
        }
    };
    __all__.__call__ = __call__;

    // Initialize non-nested modules __base__ and __standard__ and make its names available directly and via __all__
    // They can't do that itself, because they're regular Python modules
    // The compiler recognizes their names and generates them inline rather than nesting them
    // In this way it isn't needed to import them everywhere

    // __base__

    __nest__ (__all__, '', __init__ (__all__.org.transcrypt.__base__));
    var __envir__ = __all__.__envir__;

    // __standard__

    __nest__ (__all__, '', __init__ (__all__.org.transcrypt.__standard__));

    var Exception = __all__.Exception;
    var IterableError = __all__.IterableError;
    var StopIteration = __all__.StopIteration;
    var ValueError = __all__.ValueError;
    var KeyError = __all__.KeyError;
    var AssertionError = __all__.AssertionError;
    var NotImplementedError = __all__.NotImplementedError;
    var IndexError = __all__.IndexError;
    var AttributeError = __all__.AttributeError;

    // Warnings Exceptions
    var Warning = __all__.Warning;
    var UserWarning = __all__.UserWarning;
    var DeprecationWarning = __all__.DeprecationWarning;
    var RuntimeWarning = __all__.RuntimeWarning;

    var __sort__ = __all__.__sort__;
    var sorted = __all__.sorted;

    var map = __all__.map;
    var filter = __all__.filter;

    __all__.print = __all__.__terminal__.print;
    __all__.input = __all__.__terminal__.input;

    var __terminal__ = __all__.__terminal__;
    var print = __all__.print;
    var input = __all__.input;

    // Complete __envir__, that was created in __base__, for non-stub mode
    __envir__.executor_name = __envir__.transpiler_name;

    // Make make __main__ available in browser
    var __main__ = {__file__: ''};
    __all__.main = __main__;

    // Define current exception, there's at most one exception in the air at any time
    var __except__ = null;
    __all__.__except__ = __except__;
    
     // Creator of a marked dictionary, used to pass **kwargs parameter
    var __kwargtrans__ = function (anObject) {
        anObject.__kwargtrans__ = null; // Removable marker
        anObject.constructor = Object;
        return anObject;
    }
    __all__.__kwargtrans__ = __kwargtrans__;

    // 'Oneshot' dict promotor, used to enrich __all__ and help globals () return a true dict
    var __globals__ = function (anObject) {
        if (isinstance (anObject, dict)) {  // Don't attempt to promote (enrich) again, since it will make a copy
            return anObject;
        }
        else {
            return dict (anObject)
        }
    }
    __all__.__globals__ = __globals__
    
    // Partial implementation of super () .<methodName> (<params>)
    var __super__ = function (aClass, methodName) {        
        // Lean and fast, no C3 linearization, only call first implementation encountered
        // Will allow __super__ ('<methodName>') (self, <params>) rather than only <className>.<methodName> (self, <params>)
        
        for (let base of aClass.__bases__) {
            if (methodName in base) {
               return base [methodName];
            }
        }

        throw new Exception ('Superclass method not found');    // !!! Improve!
    }
    __all__.__super__ = __super__
        
    // Python property installer function, no member since that would bloat classes
    var property = function (getter, setter) {  // Returns a property descriptor rather than a property
        if (!setter) {  // ??? Make setter optional instead of dummy?
            setter = function () {};
        }
        return {get: function () {return getter (this)}, set: function (value) {setter (this, value)}, enumerable: true};
    }
    __all__.property = property;
    
    // Conditional JavaScript property installer function, prevents redefinition of properties if multiple Transcrypt apps are on one page
    var __setProperty__ = function (anObject, name, descriptor) {
        if (!anObject.hasOwnProperty (name)) {
            Object.defineProperty (anObject, name, descriptor);
        }
    }
    __all__.__setProperty__ = __setProperty__
    
    // Assert function, call to it only generated when compiling with --dassert option
    function assert (condition, message) {  // Message may be undefined
        if (!condition) {
            throw AssertionError (message, new Error ());
        }
    }

    __all__.assert = assert;

    var __merge__ = function (object0, object1) {
        var result = {};
        for (var attrib in object0) {
            result [attrib] = object0 [attrib];
        }
        for (var attrib in object1) {
            result [attrib] = object1 [attrib];
        }
        return result;
    };
    __all__.__merge__ = __merge__;

    // Manipulating attributes by name
    
    var dir = function (obj) {
        var aList = [];
        for (var aKey in obj) {
            aList.push (aKey);
        }
        aList.sort ();
        return aList;
    };
    __all__.dir = dir;

    var setattr = function (obj, name, value) {
        obj [name] = value;
    };
    __all__.setattr = setattr;

    var getattr = function (obj, name) {
        return obj [name];
    };
    __all__.getattr= getattr;

    var hasattr = function (obj, name) {
        try {
            return name in obj;
        }
        catch (exception) {
            return false;
        }
    };
    __all__.hasattr = hasattr;

    var delattr = function (obj, name) {
        delete obj [name];
    };
    __all__.delattr = (delattr);

    // The __in__ function, used to mimic Python's 'in' operator
    // In addition to CPython's semantics, the 'in' operator is also allowed to work on objects, avoiding a counterintuitive separation between Python dicts and JavaScript objects
    // In general many Transcrypt compound types feature a deliberate blend of Python and JavaScript facilities, facilitating efficient integration with JavaScript libraries
    // If only Python objects and Python dicts are dealt with in a certain context, the more pythonic 'hasattr' is preferred for the objects as opposed to 'in' for the dicts
    var __in__ = function (element, container) {
        if (py_typeof (container) == dict) {        // Currently only implemented as an augmented JavaScript object
            return container.hasOwnProperty (element);
        }
        else {                                      // Parameter 'element' itself is an array, string or a plain, non-dict JavaScript object
            return (
                container.indexOf ?                 // If it has an indexOf
                container.indexOf (element) > -1 :  // it's an array or a string,
                container.hasOwnProperty (element)  // else it's a plain, non-dict JavaScript object
            );
        }
    };
    __all__.__in__ = __in__;

    // Find out if an attribute is special
    var __specialattrib__ = function (attrib) {
        return (attrib.startswith ('__') && attrib.endswith ('__')) || attrib == 'constructor' || attrib.startswith ('py_');
    };
    __all__.__specialattrib__ = __specialattrib__;

    // Len function for any object
    var len = function (anObject) {
        if (anObject) {
            var l = anObject.length;
            if (l == undefined) {
                var result = 0;
                for (var attrib in anObject) {
                    if (!__specialattrib__ (attrib)) {
                        result++;
                    }
                }
                return result;
            }
            else {
                return l;
            }
        }
        else {
            return 0;
        }
    };
    __all__.len = len;

    // General conversions

    function __i__ (any) {  //  Conversion to iterable
        return py_typeof (any) == dict ? any.py_keys () : any;
    }

    function __t__ (any) {  // Conversion to truthyness, __ ([1, 2, 3]) returns [1, 2, 3], needed for nonempty selection: l = list1 or list2]
        return (['boolean', 'number'] .indexOf (typeof any) >= 0 || any instanceof Function || len (any)) ? any : false;
        // JavaScript functions have a length attribute, denoting the number of parameters
        // Python objects are JavaScript functions, but their length doesn't matter, only their existence
        // By the term 'any instanceof Function' we make sure that Python objects aren't rejected when their length equals zero
    }
    __all__.__t__ = __t__;

    var bool = function (any) {     // Always truly returns a bool, rather than something truthy or falsy
        return !!__t__ (any);
    };
    bool.__name__ = 'bool';         // So it can be used as a type with a name
    __all__.bool = bool;

    var float = function (any) {
        if (any == 'inf') {
            return Infinity;
        }
        else if (any == '-inf') {
            return -Infinity;
        }
        else if (isNaN (parseFloat (any))) {    // Call to parseFloat needed to exclude '', ' ' etc.
            throw ValueError (new Error ());
        }
        else {
            return +any;
        }
    };
    float.__name__ = 'float';
    __all__.float = float;

    var int = function (any) {
        return float (any) | 0
    };
    int.__name__ = 'int';
    __all__.int = int;

    var py_typeof = function (anObject) {
        var aType = typeof anObject;
        if (aType == 'object') {    // Directly trying '__class__ in anObject' turns out to wreck anObject in Chrome if its a primitive
            try {
                return anObject.__class__;
            }
            catch (exception) {
                return aType;
            }
        }
        else {
            return (    // Odly, the braces are required here
                aType == 'boolean' ? bool :
                aType == 'string' ? str :
                aType == 'number' ? (anObject % 1 == 0 ? int : float) :
                null
            );
        }
    };
    __all__.py_typeof = py_typeof;

    var isinstance = function (anObject, classinfo) {
        function isA (queryClass) {
            if (queryClass == classinfo) {
                return true;
            }
            for (var index = 0; index < queryClass.__bases__.length; index++) {
                if (isA (queryClass.__bases__ [index], classinfo)) {
                    return true;
                }
            }
            return false;
        }

        if (classinfo instanceof Array) {   // Assume in most cases it isn't, then making it recursive rather than two functions saves a call
            for (let aClass of classinfo) {
                if (isinstance (anObject, aClass)) {
                    return true;
                }
            }
            return false;
        }

        try {                   // Most frequent use case first
            return '__class__' in anObject ? isA (anObject.__class__) : anObject instanceof classinfo;
        }
        catch (exception) {     // Using isinstance on primitives assumed rare
            var aType = py_typeof (anObject);
            return aType == classinfo || (aType == bool && classinfo == int);
        }
    };
    __all__.isinstance = isinstance;

    var callable = function (anObject) {
        if ( typeof anObject == 'object' && '__call__' in anObject ) {
            return true;
        }
        else {
            return typeof anObject === 'function';
        }
    };
    __all__.callable = callable;

    // Repr function uses __repr__ method, then __str__, then toString
    var repr = function (anObject) {
        try {
            return anObject.__repr__ ();
        }
        catch (exception) {
            try {
                return anObject.__str__ ();
            }
            catch (exception) { // anObject has no __repr__ and no __str__
                try {
                    if (anObject == null) {
                        return 'None';
                    }
                    else if (anObject.constructor == Object) {
                        var result = '{';
                        var comma = false;
                        for (var attrib in anObject) {
                            if (!__specialattrib__ (attrib)) {
                                if (attrib.isnumeric ()) {
                                    var attribRepr = attrib;                // If key can be interpreted as numerical, we make it numerical
                                }                                           // So we accept that '1' is misrepresented as 1
                                else {
                                    var attribRepr = '\'' + attrib + '\'';  // Alpha key in dict
                                }

                                if (comma) {
                                    result += ', ';
                                }
                                else {
                                    comma = true;
                                }
                                result += attribRepr + ': ' + repr (anObject [attrib]);
                            }
                        }
                        result += '}';
                        return result;
                    }
                    else {
                        return typeof anObject == 'boolean' ? anObject.toString () .capitalize () : anObject.toString ();
                    }
                }
                catch (exception) {
                    console.log ('ERROR: Could not evaluate repr (<object of type ' + typeof anObject + '>)');
                    console.log (exception);
                    return '???';
                }
            }
        }
    };
    __all__.repr = repr;

    // Char from Unicode or ASCII
    var chr = function (charCode) {
        return String.fromCharCode (charCode);
    };
    __all__.chr = chr;

    // Unicode or ASCII from char
    var ord = function (aChar) {
        return aChar.charCodeAt (0);
    };
    __all__.org = ord;

    // Maximum of n numbers
    var max = Math.max;
    __all__.max = max;

    // Minimum of n numbers
    var min = Math.min;
    __all__.min = min;

    // Absolute value
    var abs = Math.abs;
    __all__.abs = abs;

    // Bankers rounding
    var round = function (number, ndigits) {
        if (ndigits) {
            var scale = Math.pow (10, ndigits);
            number *= scale;
        }

        var rounded = Math.round (number);
        if (rounded - number == 0.5 && rounded % 2) {   // Has rounded up to odd, should have rounded down to even
            rounded -= 1;
        }

        if (ndigits) {
            rounded /= scale;
        }

        return rounded;
    };
    __all__.round = round;

    // BEGIN unified iterator model

    function __jsUsePyNext__ () {       // Add as 'next' method to make Python iterator JavaScript compatible
        try {
            var result = this.__next__ ();
            return {value: result, done: false};
        }
        catch (exception) {
            return {value: undefined, done: true};
        }
    }

    function __pyUseJsNext__ () {       // Add as '__next__' method to make JavaScript iterator Python compatible
        var result = this.next ();
        if (result.done) {
            throw StopIteration (new Error ());
        }
        else {
            return result.value;
        }
    }

    function py_iter (iterable) {                   // Alias for Python's iter function, produces a universal iterator / iterable, usable in Python and JavaScript
        if (typeof iterable == 'string' || '__iter__' in iterable) {    // JavaScript Array or string or Python iterable (string has no 'in')
            var result = iterable.__iter__ ();                          // Iterator has a __next__
            result.next = __jsUsePyNext__;                              // Give it a next
        }
        else if ('selector' in iterable) {                              // Assume it's a JQuery iterator
            var result = list (iterable) .__iter__ ();                  // Has a __next__
            result.next = __jsUsePyNext__;                              // Give it a next
        }
        else if ('next' in iterable) {                                  // It's a JavaScript iterator already,  maybe a generator, has a next and may have a __next__
            var result = iterable
            if (! ('__next__' in result)) {                             // If there's no danger of recursion
                result.__next__ = __pyUseJsNext__;                      // Give it a __next__
            }
        }
        else if (Symbol.iterator in iterable) {                         // It's a JavaScript iterable such as a typed array, but not an iterator
            var result = iterable [Symbol.iterator] ();                 // Has a next
            result.__next__ = __pyUseJsNext__;                          // Give it a __next__
        }
        else {
            throw IterableError (new Error ()); // No iterator at all
        }
        result [Symbol.iterator] = function () {return result;};
        return result;
    }

    function py_next (iterator) {               // Called only in a Python context, could receive Python or JavaScript iterator
        try {                                   // Primarily assume Python iterator, for max speed
            var result = iterator.__next__ ();
        }
        catch (exception) {                     // JavaScript iterators are the exception here
            var result = iterator.next ();
            if (result.done) {
                throw StopIteration (new Error ());
            }
            else {
                return result.value;
            }
        }
        if (result == undefined) {
            throw StopIteration (new Error ());
        }
        else {
            return result;
        }
    }

    function __PyIterator__ (iterable) {
        this.iterable = iterable;
        this.index = 0;
    }

    __PyIterator__.prototype.__next__ = function () {
        if (this.index < this.iterable.length) {
            return this.iterable [this.index++];
        }
        else {
            throw StopIteration (new Error ());
        }
    };

    function __JsIterator__ (iterable) {
        this.iterable = iterable;
        this.index = 0;
    }

    __JsIterator__.prototype.next = function () {
        if (this.index < this.iterable.py_keys.length) {
            return {value: this.index++, done: false};
        }
        else {
            return {value: undefined, done: true};
        }
    };

    // END unified iterator model

    // Reversed function for arrays
    var py_reversed = function (iterable) {
        iterable = iterable.slice ();
        iterable.reverse ();
        return iterable;
    };
    __all__.py_reversed = py_reversed;

    // Zip method for arrays and strings
    var zip = function () {
        var args = [] .slice.call (arguments);
        for (var i = 0; i < args.length; i++) {
            if (typeof args [i] == 'string') {
                args [i] = args [i] .split ('');
            }
        }
        var shortest = args.length == 0 ? [] : args.reduce (    // Find shortest array in arguments
            function (array0, array1) {
                return array0.length < array1.length ? array0 : array1;
            }
        );
        return shortest.map (                   // Map each element of shortest array
            function (current, index) {         // To the result of this function
                return args.map (               // Map each array in arguments
                    function (current) {        // To the result of this function
                        return current [index]; // Namely it's index't entry
                    }
                );
            }
        );
    };
    __all__.zip = zip;

    // Range method, returning an array
    function range (start, stop, step) {
        if (stop == undefined) {
            // one param defined
            stop = start;
            start = 0;
        }
        if (step == undefined) {
            step = 1;
        }
        if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) {
            return [];
        }
        var result = [];
        for (var i = start; step > 0 ? i < stop : i > stop; i += step) {
            result.push(i);
        }
        return result;
    };
    __all__.range = range;

    // Any, all and sum

    function any (iterable) {
        for (let item of iterable) {
            if (bool (item)) {
                return true;
            }
        }
        return false;
    }
    function all (iterable) {
        for (let item of iterable) {
            if (! bool (item)) {
                return false;
            }
        }
        return true;
    }
    function sum (iterable) {
        let result = 0;
        for (let item of iterable) {
            result += item;
        }
        return result;
    }

    __all__.any = any;
    __all__.all = all;
    __all__.sum = sum;

    // Enumerate method, returning a zipped list
    function enumerate (iterable) {
        return zip (range (len (iterable)), iterable);
    }
    __all__.enumerate = enumerate;

    // Shallow and deepcopy

    function copy (anObject) {
        if (anObject == null || typeof anObject == "object") {
            return anObject;
        }
        else {
            var result = {};
            for (var attrib in obj) {
                if (anObject.hasOwnProperty (attrib)) {
                    result [attrib] = anObject [attrib];
                }
            }
            return result;
        }
    }
    __all__.copy = copy;

    function deepcopy (anObject) {
        if (anObject == null || typeof anObject == "object") {
            return anObject;
        }
        else {
            var result = {};
            for (var attrib in obj) {
                if (anObject.hasOwnProperty (attrib)) {
                    result [attrib] = deepcopy (anObject [attrib]);
                }
            }
            return result;
        }
    }
    __all__.deepcopy = deepcopy;

    // List extensions to Array

    function list (iterable) {                                      // All such creators should be callable without new
        var instance = iterable ? Array.from (iterable) : [];
        // Sort is the normal JavaScript sort, Python sort is a non-member function
        return instance;
    }
    __all__.list = list;
    Array.prototype.__class__ = list;   // All arrays are lists (not only if constructed by the list ctor), unless constructed otherwise
    list.__name__ = 'list';

    /*
    Array.from = function (iterator) { // !!! remove
        result = [];
        for (item of iterator) {
            result.push (item);
        }
        return result;
    }
    */

    Array.prototype.__iter__ = function () {return new __PyIterator__ (this);};

    Array.prototype.__getslice__ = function (start, stop, step) {
        if (start < 0) {
            start = this.length + start;
        }

        if (stop == null) {
            stop = this.length;
        }
        else if (stop < 0) {
            stop = this.length + stop;
        }
        else if (stop > this.length) {
            stop = this.length;
        }

        var result = list ([]);
        for (var index = start; index < stop; index += step) {
            result.push (this [index]);
        }

        return result;
    };

    Array.prototype.__setslice__ = function (start, stop, step, source) {
        if (start < 0) {
            start = this.length + start;
        }

        if (stop == null) {
            stop = this.length;
        }
        else if (stop < 0) {
            stop = this.length + stop;
        }

        if (step == null) { // Assign to 'ordinary' slice, replace subsequence
            Array.prototype.splice.apply (this, [start, stop - start] .concat (source));
        }
        else {              // Assign to extended slice, replace designated items one by one
            var sourceIndex = 0;
            for (var targetIndex = start; targetIndex < stop; targetIndex += step) {
                this [targetIndex] = source [sourceIndex++];
            }
        }
    };

    Array.prototype.__repr__ = function () {
        if (this.__class__ == set && !this.length) {
            return 'set()';
        }

        var result = !this.__class__ || this.__class__ == list ? '[' : this.__class__ == tuple ? '(' : '{';

        for (var index = 0; index < this.length; index++) {
            if (index) {
                result += ', ';
            }
            result += repr (this [index]);
        }

        if (this.__class__ == tuple && this.length == 1) {
            result += ',';
        }

        result += !this.__class__ || this.__class__ == list ? ']' : this.__class__ == tuple ? ')' : '}';;
        return result;
    };

    Array.prototype.__str__ = Array.prototype.__repr__;

    Array.prototype.append = function (element) {
        this.push (element);
    };

    Array.prototype.clear = function () {
        this.length = 0;
    };

    Array.prototype.extend = function (aList) {
        this.push.apply (this, aList);
    };

    Array.prototype.insert = function (index, element) {
        this.splice (index, 0, element);
    };

    Array.prototype.remove = function (element) {
        var index = this.indexOf (element);
        if (index == -1) {
            throw ValueError (new Error ());
        }
        this.splice (index, 1);
    };

    Array.prototype.index = function (element) {
        return this.indexOf (element);
    };

    Array.prototype.py_pop = function (index) {
        if (index == undefined) {
            return this.pop ();  // Remove last element
        }
        else {
            return this.splice (index, 1) [0];
        }
    };

    Array.prototype.py_sort = function () {
        __sort__.apply  (null, [this].concat ([] .slice.apply (arguments)));    // Can't work directly with arguments
        // Python params: (iterable, key = None, reverse = False)
        // py_sort is called with the Transcrypt kwargs mechanism, and just passes the params on to __sort__
        // __sort__ is def'ed with the Transcrypt kwargs mechanism
    };

    Array.prototype.__add__ = function (aList) {
        return list (this.concat (aList));
    };

    Array.prototype.__mul__ = function (scalar) {
        var result = this;
        for (var i = 1; i < scalar; i++) {
            result = result.concat (this);
        }
        return result;
    };

    Array.prototype.__rmul__ = Array.prototype.__mul__;

    // Tuple extensions to Array

    function tuple (iterable) {
        var instance = iterable ? [] .slice.apply (iterable) : [];
        instance.__class__ = tuple; // Not all arrays are tuples
        return instance;
    }
    __all__.tuple = tuple;
    tuple.__name__ = 'tuple';

    // Set extensions to Array
    // N.B. Since sets are unordered, set operations will occasionally alter the 'this' array by sorting it

    function set (iterable) {
        var instance = [];
        if (iterable) {
            for (var index = 0; index < iterable.length; index++) {
                instance.add (iterable [index]);
            }


        }
        instance.__class__ = set;   // Not all arrays are sets
        return instance;
    }
    __all__.set = set;
    set.__name__ = 'set';

    Array.prototype.__bindexOf__ = function (element) { // Used to turn O (n^2) into O (n log n)
    // Since sorting is lex, compare has to be lex. This also allows for mixed lists

        element += '';

        var mindex = 0;
        var maxdex = this.length - 1;

        while (mindex <= maxdex) {
            var index = (mindex + maxdex) / 2 | 0;
            var middle = this [index] + '';

            if (middle < element) {
                mindex = index + 1;
            }
            else if (middle > element) {
                maxdex = index - 1;
            }
            else {
                return index;
            }
        }

        return -1;
    };

    Array.prototype.add = function (element) {
        if (this.indexOf (element) == -1) { // Avoid duplicates in set
            this.push (element);
        }
    };

    Array.prototype.discard = function (element) {
        var index = this.indexOf (element);
        if (index != -1) {
            this.splice (index, 1);
        }
    };

    Array.prototype.isdisjoint = function (other) {
        this.sort ();
        for (var i = 0; i < other.length; i++) {
            if (this.__bindexOf__ (other [i]) != -1) {
                return false;
            }
        }
        return true;
    };

    Array.prototype.issuperset = function (other) {
        this.sort ();
        for (var i = 0; i < other.length; i++) {
            if (this.__bindexOf__ (other [i]) == -1) {
                return false;
            }
        }
        return true;
    };

    Array.prototype.issubset = function (other) {
        return set (other.slice ()) .issuperset (this); // Sort copy of 'other', not 'other' itself, since it may be an ordered sequence
    };

    Array.prototype.union = function (other) {
        var result = set (this.slice () .sort ());
        for (var i = 0; i < other.length; i++) {
            if (result.__bindexOf__ (other [i]) == -1) {
                result.push (other [i]);
            }
        }
        return result;
    };

    Array.prototype.intersection = function (other) {
        this.sort ();
        var result = set ();
        for (var i = 0; i < other.length; i++) {
            if (this.__bindexOf__ (other [i]) != -1) {
                result.push (other [i]);
            }
        }
        return result;
    };

    Array.prototype.difference = function (other) {
        var sother = set (other.slice () .sort ());
        var result = set ();
        for (var i = 0; i < this.length; i++) {
            if (sother.__bindexOf__ (this [i]) == -1) {
                result.push (this [i]);
            }
        }
        return result;
    };

    Array.prototype.symmetric_difference = function (other) {
        return this.union (other) .difference (this.intersection (other));
    };

    Array.prototype.py_update = function () {   // O (n)
        var updated = [] .concat.apply (this.slice (), arguments) .sort ();
        this.clear ();
        for (var i = 0; i < updated.length; i++) {
            if (updated [i] != updated [i - 1]) {
                this.push (updated [i]);
            }
        }
    };

    Array.prototype.__eq__ = function (other) { // Also used for list
        if (this.length != other.length) {
            return false;
        }
        if (this.__class__ == set) {
            this.sort ();
            other.sort ();
        }
        for (var i = 0; i < this.length; i++) {
            if (this [i] != other [i]) {
                return false;
            }
        }
        return true;
    };

    Array.prototype.__ne__ = function (other) { // Also used for list
        return !this.__eq__ (other);
    };

    Array.prototype.__le__ = function (other) {
        return this.issubset (other);
    };

    Array.prototype.__ge__ = function (other) {
        return this.issuperset (other);
    };

    Array.prototype.__lt__ = function (other) {
        return this.issubset (other) && !this.issuperset (other);
    };

    Array.prototype.__gt__ = function (other) {
        return this.issuperset (other) && !this.issubset (other);
    };

    // String extensions

    function str (stringable) {
        try {
            return stringable.__str__ ();
        }
        catch (exception) {
            try {
                return repr (stringable);
            }
            catch (exception) {
                return String (stringable); // No new, so no permanent String object but a primitive in a temporary 'just in time' wrapper
            }
        }
    };
    __all__.str = str;

    String.prototype.__class__ = str;   // All strings are str
    str.__name__ = 'str';

    String.prototype.__iter__ = function () {new __PyIterator__ (this);};

    String.prototype.__repr__ = function () {
        return (this.indexOf ('\'') == -1 ? '\'' + this + '\'' : '"' + this + '"') .py_replace ('\t', '\\t') .py_replace ('\n', '\\n');
    };

    String.prototype.__str__ = function () {
        return this;
    };

    String.prototype.capitalize = function () {
        return this.charAt (0).toUpperCase () + this.slice (1);
    };

    String.prototype.endswith = function (suffix) {
        return suffix == '' || this.slice (-suffix.length) == suffix;
    };

    String.prototype.find  = function (sub, start) {
        return this.indexOf (sub, start);
    };

    String.prototype.__getslice__ = function (start, stop, step) {
        if (start < 0) {
            start = this.length + start;
        }

        if (stop == null) {
            stop = this.length;
        }
        else if (stop < 0) {
            stop = this.length + stop;
        }

        var result = '';
        if (step == 1) {
            result = this.substring (start, stop);
        }
        else {
            for (var index = start; index < stop; index += step) {
                result = result.concat (this.charAt(index));
            }
        }
        return result;
    }

    // Since it's worthwhile for the 'format' function to be able to deal with *args, it is defined as a property
    // __get__ will produce a bound function if there's something before the dot
    // Since a call using *args is compiled to e.g. <object>.<function>.apply (null, args), the function has to be bound already
    // Otherwise it will never be, because of the null argument
    // Using 'this' rather than 'null' contradicts the requirement to be able to pass bound functions around
    // The object 'before the dot' won't be available at call time in that case, unless implicitly via the function bound to it
    // While for Python methods this mechanism is generated by the compiler, for JavaScript methods it has to be provided manually
    // Call memoizing is unattractive here, since every string would then have to hold a reference to a bound format method
    __setProperty__ (String.prototype, 'format', {
        get: function () {return __get__ (this, function (self) {
            var args = tuple ([] .slice.apply (arguments).slice (1));
            var autoIndex = 0;
            return self.replace (/\{(\w*)\}/g, function (match, key) {
                if (key == '') {
                    key = autoIndex++;
                }
                if (key == +key) {  // So key is numerical
                    return args [key] == undefined ? match : str (args [key]);
                }
                else {              // Key is a string
                    for (var index = 0; index < args.length; index++) {
                        // Find first 'dict' that has that key and the right field
                        if (typeof args [index] == 'object' && args [index][key] != undefined) {
                            return str (args [index][key]); // Return that field field
                        }
                    }
                    return match;
                }
            });
        });},
        enumerable: true
    });

    String.prototype.isnumeric = function () {
        return !isNaN (parseFloat (this)) && isFinite (this);
    };

    String.prototype.join = function (strings) {
        strings = Array.from (strings); // Much faster than iterating through strings char by char
        return strings.join (this);
    };

    String.prototype.lower = function () {
        return this.toLowerCase ();
    };

    String.prototype.py_replace = function (old, aNew, maxreplace) {
        return this.split (old, maxreplace) .join (aNew);
    };

    String.prototype.lstrip = function () {
        return this.replace (/^\s*/g, '');
    };

    String.prototype.rfind = function (sub, start) {
        return this.lastIndexOf (sub, start);
    };

    String.prototype.rsplit = function (sep, maxsplit) {    // Combination of general whitespace sep and positive maxsplit neither supported nor checked, expensive and rare
        if (sep == undefined || sep == null) {
            sep = /\s+/;
            var stripped = this.strip ();
        }
        else {
            var stripped = this;
        }

        if (maxsplit == undefined || maxsplit == -1) {
            return stripped.split (sep);
        }
        else {
            var result = stripped.split (sep);
            if (maxsplit < result.length) {
                var maxrsplit = result.length - maxsplit;
                return [result.slice (0, maxrsplit) .join (sep)] .concat (result.slice (maxrsplit));
            }
            else {
                return result;
            }
        }
    };

    String.prototype.rstrip = function () {
        return this.replace (/\s*$/g, '');
    };

    String.prototype.py_split = function (sep, maxsplit) {  // Combination of general whitespace sep and positive maxsplit neither supported nor checked, expensive and rare
        if (sep == undefined || sep == null) {
            sep = /\s+/;
            var stripped = this.strip ();
        }
        else {
            var stripped = this;
        }

        if (maxsplit == undefined || maxsplit == -1) {
            return stripped.split (sep);
        }
        else {
            var result = stripped.split (sep);
            if (maxsplit < result.length) {
                return result.slice (0, maxsplit).concat ([result.slice (maxsplit).join (sep)]);
            }
            else {
                return result;
            }
        }
    };

    String.prototype.startswith = function (prefix) {
        return this.indexOf (prefix) == 0;
    };

    String.prototype.strip = function () {
        return this.trim ();
    };

    String.prototype.upper = function () {
        return this.toUpperCase ();
    };

    String.prototype.__mul__ = function (scalar) {
        var result = this;
        for (var i = 1; i < scalar; i++) {
            result = result + this;
        }
        return result;
    };

    String.prototype.__rmul__ = String.prototype.__mul__;

    // Dict extensions to object

    function __keys__ () {
        var keys = [];
        for (var attrib in this) {
            if (!__specialattrib__ (attrib)) {
                keys.push (attrib);
            }
        }
        return keys;
    }

    function __items__ () {
        var items = [];
        for (var attrib in this) {
            if (!__specialattrib__ (attrib)) {
                items.push ([attrib, this [attrib]]);
            }
        }
        return items;
    }

    function __del__ (key) {
        delete this [key];
    }

    function __clear__ () {
        for (var attrib in this) {
            delete this [attrib];
        }
    }

    function __getdefault__ (aKey, aDefault) {  // Each Python object already has a function called __get__, so we call this one __getdefault__
        var result = this [aKey];
        return result == undefined ? (aDefault == undefined ? null : aDefault) : result;
    }

    function __setdefault__ (aKey, aDefault) {
        var result = this [aKey];
        if (result != undefined) {
            return result;
        }
        var val = aDefault == undefined ? null : aDefault;
        this [aKey] = val;
        return val;
    }

    function __pop__ (aKey, aDefault) {
        var result = this [aKey];
        if (result != undefined) {
            delete this [aKey];
            return result;
        } else {
            // Identify check because user could pass None
            if ( aDefault === undefined ) {
                throw KeyError (aKey, new Error());
            }
        }
        return aDefault;
    }
    
    function __popitem__ () {
        var aKey = Object.keys (this) [0];
        if (aKey == null) {
            throw KeyError (aKey, new Error ());
        }
        var result = tuple ([aKey, this [aKey]]);
        delete this [aKey];
        return result;
    }
    
    function __update__ (aDict) {
        for (var aKey in aDict) {
            this [aKey] = aDict [aKey];
        }
    }
    
    function __values__ () {
        var values = [];
        for (var attrib in this) {
            if (!__specialattrib__ (attrib)) {
                values.push (this [attrib]);
            }
        }
        return values;

    }
    
    function __dgetitem__ (aKey) {
        return this [aKey];
    }
    
    function __dsetitem__ (aKey, aValue) {
        this [aKey] = aValue;
    }

    function dict (objectOrPairs) {
        var instance = {};
        if (!objectOrPairs || objectOrPairs instanceof Array) { // It's undefined or an array of pairs
            if (objectOrPairs) {
                for (var index = 0; index < objectOrPairs.length; index++) {
                    var pair = objectOrPairs [index];
                    if ( !(pair instanceof Array) || pair.length != 2) {
                        throw ValueError(
                            "dict update sequence element #" + index +
                            " has length " + pair.length +
                            "; 2 is required", new Error());
                    }
                    var key = pair [0];
                    var val = pair [1];
                    if (!(objectOrPairs instanceof Array) && objectOrPairs instanceof Object) {
                         // User can potentially pass in an object
                         // that has a hierarchy of objects. This
                         // checks to make sure that these objects
                         // get converted to dict objects instead of
                         // leaving them as js objects.
                         
                         if (!isinstance (objectOrPairs, dict)) {
                             val = dict (val);
                         }
                    }
                    instance [key] = val;
                }
            }
        }
        else {
            if (isinstance (objectOrPairs, dict)) {
                // Passed object is a dict already so we need to be a little careful
                // N.B. - this is a shallow copy per python std - so
                // it is assumed that children have already become
                // python objects at some point.
                
                var aKeys = objectOrPairs.py_keys ();
                for (var index = 0; index < aKeys.length; index++ ) {
                    var key = aKeys [index];
                    instance [key] = objectOrPairs [key];
                }
            } else if (objectOrPairs instanceof Object) {
                // Passed object is a JavaScript object but not yet a dict, don't copy it
                instance = objectOrPairs;
            } else {
                // We have already covered Array so this indicates
                // that the passed object is not a js object - i.e.
                // it is an int or a string, which is invalid.
                
                throw ValueError ("Invalid type of object for dict creation", new Error ());
            }
        }

        // Trancrypt interprets e.g. {aKey: 'aValue'} as a Python dict literal rather than a JavaScript object literal
        // So dict literals rather than bare Object literals will be passed to JavaScript libraries
        // Some JavaScript libraries call all enumerable callable properties of an object that's passed to them
        // So the properties of a dict should be non-enumerable
        __setProperty__ (instance, '__class__', {value: dict, enumerable: false, writable: true});
        __setProperty__ (instance, 'py_keys', {value: __keys__, enumerable: false});
        __setProperty__ (instance, '__iter__', {value: function () {new __PyIterator__ (this.py_keys ());}, enumerable: false});
        __setProperty__ (instance, Symbol.iterator, {value: function () {new __JsIterator__ (this.py_keys ());}, enumerable: false});
        __setProperty__ (instance, 'py_items', {value: __items__, enumerable: false});
        __setProperty__ (instance, 'py_del', {value: __del__, enumerable: false});
        __setProperty__ (instance, 'py_clear', {value: __clear__, enumerable: false});
        __setProperty__ (instance, 'py_get', {value: __getdefault__, enumerable: false});
        __setProperty__ (instance, 'py_setdefault', {value: __setdefault__, enumerable: false});
        __setProperty__ (instance, 'py_pop', {value: __pop__, enumerable: false});
        __setProperty__ (instance, 'py_popitem', {value: __popitem__, enumerable: false});
        __setProperty__ (instance, 'py_update', {value: __update__, enumerable: false});
        __setProperty__ (instance, 'py_values', {value: __values__, enumerable: false});
        __setProperty__ (instance, '__getitem__', {value: __dgetitem__, enumerable: false});    // Needed since compound keys necessarily
        __setProperty__ (instance, '__setitem__', {value: __dsetitem__, enumerable: false});    // trigger overloading to deal with slices
        return instance;
    }

    __all__.dict = dict;
    dict.__name__ = 'dict';
    
    // Docstring setter

    function __setdoc__ (docString) {
        this.__doc__ = docString;
        return this;
    }

    // Python classes, methods and functions are all translated to JavaScript functions
    __setProperty__ (Function.prototype, '__setdoc__', {value: __setdoc__, enumerable: false});

    // General operator overloading, only the ones that make most sense in matrix and complex operations

    var __neg__ = function (a) {
        if (typeof a == 'object' && '__neg__' in a) {
            return a.__neg__ ();
        }
        else {
            return -a;
        }
    };
    __all__.__neg__ = __neg__;

    var __matmul__ = function (a, b) {
        return a.__matmul__ (b);
    };
    __all__.__matmul__ = __matmul__;

    var __pow__ = function (a, b) {
        if (typeof a == 'object' && '__pow__' in a) {
            return a.__pow__ (b);
        }
        else if (typeof b == 'object' && '__rpow__' in b) {
            return b.__rpow__ (a);
        }
        else {
            return Math.pow (a, b);
        }
    };
    __all__.pow = __pow__;

    var __jsmod__ = function (a, b) {
        if (typeof a == 'object' && '__mod__' in a) {
            return a.__mod__ (b);
        }
        else if (typeof b == 'object' && '__rpow__' in b) {
            return b.__rmod__ (a);
        }
        else {
            return a % b;
        }
    };
    __all__.__jsmod__ = __jsmod__;
    
    var __mod__ = function (a, b) {
        if (typeof a == 'object' && '__mod__' in a) {
            return a.__mod__ (b);
        }
        else if (typeof b == 'object' && '__rpow__' in b) {
            return b.__rmod__ (a);
        }
        else {
            return ((a % b) + b) % b;
        }
    };
    __all__.mod = __mod__;

    // Overloaded binary arithmetic
    
    var __mul__ = function (a, b) {
        if (typeof a == 'object' && '__mul__' in a) {
            return a.__mul__ (b);
        }
        else if (typeof b == 'object' && '__rmul__' in b) {
            return b.__rmul__ (a);
        }
        else if (typeof a == 'string') {
            return a.__mul__ (b);
        }
        else if (typeof b == 'string') {
            return b.__rmul__ (a);
        }
        else {
            return a * b;
        }
    };
    __all__.__mul__ = __mul__;

    var __div__ = function (a, b) {
        if (typeof a == 'object' && '__div__' in a) {
            return a.__div__ (b);
        }
        else if (typeof b == 'object' && '__rdiv__' in b) {
            return b.__rdiv__ (a);
        }
        else {
            return a / b;
        }
    };
    __all__.__div__ = __div__;

    var __add__ = function (a, b) {
        if (typeof a == 'object' && '__add__' in a) {
            return a.__add__ (b);
        }
        else if (typeof b == 'object' && '__radd__' in b) {
            return b.__radd__ (a);
        }
        else {
            return a + b;
        }
    };
    __all__.__add__ = __add__;

    var __sub__ = function (a, b) {
        if (typeof a == 'object' && '__sub__' in a) {
            return a.__sub__ (b);
        }
        else if (typeof b == 'object' && '__rsub__' in b) {
            return b.__rsub__ (a);
        }
        else {
            return a - b;
        }
    };
    __all__.__sub__ = __sub__;

    // Overloaded binary bitwise
    
    var __lshift__ = function (a, b) {
        if (typeof a == 'object' && '__lshift__' in a) {
            return a.__lshift__ (b);
        }
        else if (typeof b == 'object' && '__rlshift__' in b) {
            return b.__rlshift__ (a);
        }
        else {
            return a << b;
        }
    };
    __all__.__lshift__ = __lshift__;

    var __rshift__ = function (a, b) {
        if (typeof a == 'object' && '__rshift__' in a) {
            return a.__rshift__ (b);
        }
        else if (typeof b == 'object' && '__rrshift__' in b) {
            return b.__rrshift__ (a);
        }
        else {
            return a >> b;
        }
    };
    __all__.__rshift__ = __rshift__;

    var __or__ = function (a, b) {
        if (typeof a == 'object' && '__or__' in a) {
            return a.__or__ (b);
        }
        else if (typeof b == 'object' && '__ror__' in b) {
            return b.__ror__ (a);
        }
        else {
            return a | b;
        }
    };
    __all__.__or__ = __or__;

    var __xor__ = function (a, b) {
        if (typeof a == 'object' && '__xor__' in a) {
            return a.__xor__ (b);
        }
        else if (typeof b == 'object' && '__rxor__' in b) {
            return b.__rxor__ (a);
        }
        else {
            return a ^ b;
        }
    };
    __all__.__xor__ = __xor__;

    var __and__ = function (a, b) {
        if (typeof a == 'object' && '__and__' in a) {
            return a.__and__ (b);
        }
        else if (typeof b == 'object' && '__rand__' in b) {
            return b.__rand__ (a);
        }
        else {
            return a & b;
        }
    };
    __all__.__and__ = __and__;    
        
    // Overloaded binary compare
    
    var __eq__ = function (a, b) {
        if (typeof a == 'object' && '__eq__' in a) {
            return a.__eq__ (b);
        }
        else {
            return a == b;
        }
    };
    __all__.__eq__ = __eq__;

    var __ne__ = function (a, b) {
        if (typeof a == 'object' && '__ne__' in a) {
            return a.__ne__ (b);
        }
        else {
            return a != b
        }
    };
    __all__.__ne__ = __ne__;

    var __lt__ = function (a, b) {
        if (typeof a == 'object' && '__lt__' in a) {
            return a.__lt__ (b);
        }
        else {
            return a < b;
        }
    };
    __all__.__lt__ = __lt__;

    var __le__ = function (a, b) {
        if (typeof a == 'object' && '__le__' in a) {
            return a.__le__ (b);
        }
        else {
            return a <= b;
        }
    };
    __all__.__le__ = __le__;

    var __gt__ = function (a, b) {
        if (typeof a == 'object' && '__gt__' in a) {
            return a.__gt__ (b);
        }
        else {
            return a > b;
        }
    };
    __all__.__gt__ = __gt__;

    var __ge__ = function (a, b) {
        if (typeof a == 'object' && '__ge__' in a) {
            return a.__ge__ (b);
        }
        else {
            return a >= b;
        }
    };
    __all__.__ge__ = __ge__;
    
    // Overloaded augmented general
    
    var __imatmul__ = function (a, b) {
        if ('__imatmul__' in a) {
            return a.__imatmul__ (b);
        }
        else {
            return a.__matmul__ (b);
        }
    };
    __all__.__imatmul__ = __imatmul__;

    var __ipow__ = function (a, b) {
        if (typeof a == 'object' && '__pow__' in a) {
            return a.__ipow__ (b);
        }
        else if (typeof a == 'object' && '__ipow__' in a) {
            return a.__pow__ (b);
        }
        else if (typeof b == 'object' && '__rpow__' in b) {
            return b.__rpow__ (a);
        }
        else {
            return Math.pow (a, b);
        }
    };
    __all__.ipow = __ipow__;

    var __ijsmod__ = function (a, b) {
        if (typeof a == 'object' && '__imod__' in a) {
            return a.__ismod__ (b);
        }
        else if (typeof a == 'object' && '__mod__' in a) {
            return a.__mod__ (b);
        }
        else if (typeof b == 'object' && '__rpow__' in b) {
            return b.__rmod__ (a);
        }
        else {
            return a % b;
        }
    };
    __all__.ijsmod__ = __ijsmod__;
    
    var __imod__ = function (a, b) {
        if (typeof a == 'object' && '__imod__' in a) {
            return a.__imod__ (b);
        }
        else if (typeof a == 'object' && '__mod__' in a) {
            return a.__mod__ (b);
        }
        else if (typeof b == 'object' && '__rpow__' in b) {
            return b.__rmod__ (a);
        }
        else {
            return ((a % b) + b) % b;
        }
    };
    __all__.imod = __imod__;
    
    // Overloaded augmented arithmetic
    
    var __imul__ = function (a, b) {
        if (typeof a == 'object' && '__imul__' in a) {
            return a.__imul__ (b);
        }
        else if (typeof a == 'object' && '__mul__' in a) {
            return a = a.__mul__ (b);
        }
        else if (typeof b == 'object' && '__rmul__' in b) {
            return a = b.__rmul__ (a);
        }
        else if (typeof a == 'string') {
            return a = a.__mul__ (b);
        }
        else if (typeof b == 'string') {
            return a = b.__rmul__ (a);
        }
        else {
            return a *= b;
        }
    };
    __all__.__imul__ = __imul__;

    var __idiv__ = function (a, b) {
        if (typeof a == 'object' && '__idiv__' in a) {
            return a.__idiv__ (b);
        }
        else if (typeof a == 'object' && '__div__' in a) {
            return a = a.__div__ (b);
        }
        else if (typeof b == 'object' && '__rdiv__' in b) {
            return a = b.__rdiv__ (a);
        }
        else {
            return a /= b;
        }
    };
    __all__.__idiv__ = __idiv__;

    var __iadd__ = function (a, b) {
        if (typeof a == 'object' && '__iadd__' in a) {
            return a.__iadd__ (b);
        }
        else if (typeof a == 'object' && '__add__' in a) {
            return a = a.__add__ (b);
        }
        else if (typeof b == 'object' && '__radd__' in b) {
            return a = b.__radd__ (a);
        }
        else {
            return a += b;
        }
    };
    __all__.__iadd__ = __iadd__;

    var __isub__ = function (a, b) {
        if (typeof a == 'object' && '__isub__' in a) {
            return a.__isub__ (b);
        }
        else if (typeof a == 'object' && '__sub__' in a) {
            return a = a.__sub__ (b);
        }
        else if (typeof b == 'object' && '__rsub__' in b) {
            return a = b.__rsub__ (a);
        }
        else {
            return a -= b;
        }
    };
    __all__.__isub__ = __isub__;

    // Overloaded augmented bitwise
    
    var __ilshift__ = function (a, b) {
        if (typeof a == 'object' && '__ilshift__' in a) {
            return a.__ilshift__ (b);
        }
        else if (typeof a == 'object' && '__lshift__' in a) {
            return a = a.__lshift__ (b);
        }
        else if (typeof b == 'object' && '__rlshift__' in b) {
            return a = b.__rlshift__ (a);
        }
        else {
            return a <<= b;
        }
    };
    __all__.__ilshift__ = __ilshift__;

    var __irshift__ = function (a, b) {
        if (typeof a == 'object' && '__irshift__' in a) {
            return a.__irshift__ (b);
        }
        else if (typeof a == 'object' && '__rshift__' in a) {
            return a = a.__rshift__ (b);
        }
        else if (typeof b == 'object' && '__rrshift__' in b) {
            return a = b.__rrshift__ (a);
        }
        else {
            return a >>= b;
        }
    };
    __all__.__irshift__ = __irshift__;

    var __ior__ = function (a, b) {
        if (typeof a == 'object' && '__ior__' in a) {
            return a.__ior__ (b);
        }
        else if (typeof a == 'object' && '__or__' in a) {
            return a = a.__or__ (b);
        }
        else if (typeof b == 'object' && '__ror__' in b) {
            return a = b.__ror__ (a);
        }
        else {
            return a |= b;
        }
    };
    __all__.__ior__ = __ior__;

    var __ixor__ = function (a, b) {
        if (typeof a == 'object' && '__ixor__' in a) {
            return a.__ixor__ (b);
        }
        else if (typeof a == 'object' && '__xor__' in a) {
            return a = a.__xor__ (b);
        }
        else if (typeof b == 'object' && '__rxor__' in b) {
            return a = b.__rxor__ (a);
        }
        else {
            return a ^= b;
        }
    };
    __all__.__ixor__ = __ixor__;

    var __iand__ = function (a, b) {
        if (typeof a == 'object' && '__iand__' in a) {
            return a.__iand__ (b);
        }
        else if (typeof a == 'object' && '__and__' in a) {
            return a = a.__and__ (b);
        }
        else if (typeof b == 'object' && '__rand__' in b) {
            return a = b.__rand__ (a);
        }
        else {
            return a &= b;
        }
    };
    __all__.__iand__ = __iand__;
    
    // Indices and slices

    var __getitem__ = function (container, key) {                           // Slice c.q. index, direct generated call to runtime switch
        if (typeof container == 'object' && '__getitem__' in container) {
            return container.__getitem__ (key);                             // Overloaded on container
        }
        else {
            return container [key];                                         // Container must support bare JavaScript brackets
        }
    };
    __all__.__getitem__ = __getitem__;

    var __setitem__ = function (container, key, value) {                    // Slice c.q. index, direct generated call to runtime switch
        if (typeof container == 'object' && '__setitem__' in container) {
            container.__setitem__ (key, value);                             // Overloaded on container
        }
        else {
            container [key] = value;                                        // Container must support bare JavaScript brackets
        }
    };
    __all__.__setitem__ = __setitem__;

    var __getslice__ = function (container, lower, upper, step) {           // Slice only, no index, direct generated call to runtime switch
        if (typeof container == 'object' && '__getitem__' in container) {
            return container.__getitem__ ([lower, upper, step]);            // Container supports overloaded slicing c.q. indexing
        }
        else {
            return container.__getslice__ (lower, upper, step);             // Container only supports slicing injected natively in prototype
        }
    };
    __all__.__getslice__ = __getslice__;

    var __setslice__ = function (container, lower, upper, step, value) {    // Slice, no index, direct generated call to runtime switch
        if (typeof container == 'object' && '__setitem__' in container) {
            container.__setitem__ ([lower, upper, step], value);            // Container supports overloaded slicing c.q. indexing
        }
        else {
            container.__setslice__ (lower, upper, step, value);             // Container only supports slicing injected natively in prototype
        }
    };
    __all__.__setslice__ = __setslice__;

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
   return __all__;
}
window ['pages'] = pages ();

//# sourceMappingURL=extra/sourcemap/pages.js.map
