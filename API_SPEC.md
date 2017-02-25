# Happypanda X Server API specification
## General
----
Message Protocol: `JSON`
> TODO: needs more details

> Pay attention to the value data types

Every message must provide two root keys, namely, `name` and `data`. After `name` has been specified, everything goes inside `data`:
```json
{
	'name': 'server',
	'data': {}
}
```

Functions are invoked with the `function` keyword. In it, a dict with `fname` key to specify function name is required.
Additional function parameters are provided in this dict as key:value pairs:
```json
{
	'name':string,
	'data': {
		'function': {
			'fname': 'get_gallery',
			'galleryid': 2
		}
	}
}
```

**Note:** *from here on only examples inside the `data` dict will be shown.

## Objects
>These are the objects Happypanda X will be using and expecting

### `msg` 
> A string based message, useful for an arbitrary remark

```json
	'msg': "this is a remark"
```

### `error` 
> An error

```json
	'error': {
		'code': 321,
		'msg': "An error occured!"
	}
```

### gallery 
> TODO
> A gallery object, or list

```json

		{
			'title': "Gallery 1"
		}

```

## API

### Version 0
-----
#### add_gallery(galleries=[], paths=[])
*Add galleries from list of paths or gallery objects*  
**Note**: *Paths to galleries must be local to the server*

**Returns:**  
```json
	'function': {
		'fname': "get_gallery",
		'galleries': [] # a list of galleries
		'paths': [] # a list of paths
	}

```

**Example:**  
with `galleries` parameter:
```json
{
	'function': {
		'fname': "get_gallery",
		'galleries': [ 
			{
				'title': 'Gallery 1',
				...
			},

			{
				'title': 'Gallery 2',
				...
			}
		]
	}
}
```
with `paths` parameter:
```json
	'function': {
		'fname': "get_gallery",
		'paths': [ 
			"path/to/gallery1",
			"path/to/gallery2",
			"path/to/gallery3"
		]
	}

```


