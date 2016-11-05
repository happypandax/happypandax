## This is Happypanda Server API specification
### General
----
Message Protocol: `XML`
> needs more details

Every message must have the `<hp>` as root element, and specify the API version with the `api` attribute:
```xml
<hp api='0'>
</hp>
```

Functions are invoked with the `<function>` element with `fname` attribute to specify name of function. Additional attributes will be treated as function arguments:
```xml
<hp api='0'>
    <function fname='getGallery' galleryid='0'>
    </function>
</hp>
```

**Note:** *from here on `<hp>` will be omitted, but should still be considered part of the message*

###### Types & Objects
**Base types**  
`<string>`: a string  
`<int>`: an integer  
`<timestamp>`: a timestamp  

***Note:*** *defaults to `<string>` if no type is specified*

**Objects**  
> TODO
`<status>`:
```xml
<status>
    <error></error>
</status>
```

> TODO
`<gallery>`:
```xml
<gallery>
    <title></title>
</gallery>
```

###### Parameter Code
`optional`: *this parameter is optional*  
`OR` : *this parameter is only optional if other parameters are used*  
`XOR` : *if this parameter is used no other parameters can be used*  
`required`: *this parameter is required*  

### Version 0
-----
###### addGallery(gallery_objects=XOR, paths=XOR)
*Add gallery or galleries from list of paths or gallery objects*  
**Note**: *Paths to galleries must exist on server system*

**Example:**  
`gallery_objects`:
```xml
<function fname='addGallery' param='gallery_objects'>
    <gallery>...</gallery>
    <gallery>...</gallery>
    <gallery>...</gallery>
<function>

```
`paths`:
```xml
<function fname='addGallery' param='paths'>
    <string>C:\path\to\gallery1</string>
    <string>C:\path\to\gallery2</string>
    <string>C:\path\to\gallery3</string>
<function>

```

**Returns:**  
`gallery_objects` -- `status`  
`paths` -- `<gallery> objects`  


