[![PyPI version](https://badge.fury.io/py/django-parcel-ssr.svg)](https://badge.fury.io/py/django-parcel-ssr)

# Django Parcel SSR

Zero configuration performant JavaScript server side rendering for [Django web framework](https://www.djangoproject.com/), powered by [Parcel bundler](https://parceljs.org/). 

## Install

```bash
pip install django-parcel-ssr
npm install parcel-bundler
```

[React](https://reactjs.org/) is supported out of the box, but any JavaScript view library with server side rendering support can be used instead (see `scripts` option and [examples](examples)). To use React install additional dependencies:

```bash
npm install react react-dom react-helmet styled-jsx
```

Default React setup comes with optional [`styled-jsx`](https://github.com/zeit/styled-jsx) CSS-in-JS support for writing CSS which applies only to a single component. To use it, add the `.babelrc` file with the plugin to your project root:

```json
{
    "plugins": [
        "styled-jsx/babel"
    ]
}
```

**Note for TypeScript users**: Parcel 1.x doesn't support Babel plugins for TypeScript out the box. Check out the [TypeScript example](examples/typescript.md) for a workaround.

Update `INSTALLED_APPS`, `TEMPLATES`, and `STATICFILES_DIRS` entries in `settings.py`:

```python
INSTALLED_APPS = [
    'ssr',
    # ...
]

TEMPLATES = [
    {
        'BACKEND': 'ssr.backends.javascript.Components',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            # 'extensions': ['js', 'jsx', 'ts', 'tsx'],
            # 'output_dirname': 'dist/',
            # 'json_encoder': 'django.core.serializers.json.DjangoJSONEncoder',
            # 'cache': True,
            # 'env': {
            #     'NODE_ENV': 'development' if DEBUG else 'production',
            #     'NODE_OPTIONS': '--experimental-modules --no-warnings',
            #     'WORKER_TTL': 1000,
            # },
            # 'scripts': {
            #     'server': os.path.join(BASE_DIR, '.ssr', 'scripts', 'react', 'server.js'),
            #     'client': os.path.join(BASE_DIR, '.ssr', 'scripts', 'react', 'client.js'),
            # }
        }
    },
    # ...
]

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, '.ssr', 'static'),
    # ...
)
```

Initialize server side rendering in `wsgi.py`:

```python
# ...
import ssr
ssr.setup()
```

We recommend adding `.ssr/` directory to `.gitignore`, to avoid committing your builds.

## Usage

JavaScript files in `bundles` directories of installed Django apps serve as Parcel entry points and they have to provide a root component as default export. **Avoid putting non root components in `bundles` directories** to prevent unnecessary bundling:

- `bundles/`
    - `template.js`
- `components/`
    - `layout.js`
    - `navbar.js`
    - `...`

Create an example `bundles/template.js` file in an installed app directory:

```javascript
import React from 'react'
import { Helmet } from 'react-helmet'

export default props => {
    const [count, setCount] = React.useState(props.count)
    return (
        <div>
            <Helmet>
                <title>{props.title}</title>
            </Helmet>

            <h1>Count: {count}</h1>
            <button onClick={() => setCount(count + 1)}>+</button>
            <button onClick={() => setCount(count - 1)}>-</button>
            
            <style jsx>{`
                h1 {
                    color: ${props.color};
                }
            `}</style>
        </div>
    )
}
```

Bundles are available to the templating engine for server side rendering, but **context has to be JSON serializable** (see restrictions below).

Create an example Django view in `urls.py`:

```python
from django.urls import path
from django.shortcuts import render

def react_view(request):
    return render(request, 'template.js', context={
        'title': 'Django SSR'
        'count': 0,
        'color': 'red'
    })
    
urlpatterns = [
    # ...
    path('', react_view)
]
```

Run `./manage.py runserver` and navigate to `http://localhost:8000`.

Consult [Parcel documentation](https://parceljs.org/getting_started.html) to learn about supported assets, recipes, and more.

### Restrictions

Template context has to be a JSON serializable value because the actual rendering is handled by JavaScript. Django objects have to be [serialized](https://docs.djangoproject.com/en/2.1/topics/serialization/#serialization-formats-json); querysets can be rendered as dictionaries instead of model instances using [`QuerySet.values()`](https://docs.djangoproject.com/en/2.1/ref/models/querysets/#values). For advanced use cases such as handling model relations, serialize context data manually, e.g. using Django REST Framework's [model serializer](https://www.django-rest-framework.org/api-guide/serializers/#modelserializer).


## Deployment

If `NODE_ENV` option is set to `production` (by default this happens when `DEBUG = False`), starting the Django app will not automatically bundle entry points. You'll need to invoke the management command manually, and collect staticfiles afterwards:

```bash
./manage.py bundle
./manage.py collectstatic -l
```

## Options

### extensions

Default: `['js', 'jsx', 'ts', 'tsx']`

List of valid file extensions for bundles. 

### output_dirname

Default: `'dist/'`

Name of the Parcel bundles output directory. **Trailing slash is required.**

### json_encoder

Default: `'django.core.serializers.json.DjangoJSONEncoder'`

JSON encoder class used for serializing view context into props. 

### cache

Default: `True`

Enables or disables Parcel bundler caching.

### env.NODE_ENV

Default: `'development' if DEBUG else 'production'`

Development mode activates bundle watchers with HMR (hot module replacement). Production mode performs a single build and outputs optimized bundles.

### env.NODE_OPTIONS

Default: `'--experimental-modules --no-warnings'`

CLI options for Node workers. 

Server side renderer uses experimental [ECMAScript modules](https://nodejs.org/docs/latest/api/esm.html) loader to handle dynamic imports, only available in Node 10+. If you require support for older versions of Node, [`esm`](https://github.com/standard-things/esm) loader can be used instead:

```bash
npm install esm
```

Add it to `settings.py`:

```python
'OPTIONS': {
    'env': {
        'NODE_OPTIONS': '-r esm'
    }
}
```

### env.WORKER_TTL

Default: `1000`

Number of milliseconds Node workers will wait for Django to restart before exiting. 

### scripts.server

Default: `'{BASE_DIR}/.ssr/scripts/react/server.js'`

Absolute path to custom `createRenderer` function, used to create `render` function which has to return HTML document string. This file is transpiled and executed on the server.

```javascript
import { createElement, renderToString } from 'some-view-library'

export default Component => ({ script, stylesheet }, props) => {
    const component = createElement(Component, props)
    const html = renderToString(component)
    const serializedProps = encodeURIComponent(JSON.stringify(props))
    return `
        <!DOCTYPE html>
        <head>
            <!-- ... -->
            ${stylesheet && `<link src="${stylesheet}" rel="stylesheet">`}
        </head>
        <body>
            <div id="root" data-props="${serializedProps}">${html}</div>
            <script src="${script}"></script>
        </body>
    `
}
```

### scripts.client

Default: `'{BASE_DIR}/.ssr/scripts/react/client.js'`

Absolute path to custom `hydrate` function, used to update the root DOM node when the page loads. This file is transpiled and executed in the browser.

```javascript
import { createElement, hydrate } from 'some-view-library'

export default Component => {
    const root = document.getElementById('root')
    const props = JSON.parse(decodeURIComponent(root.dataset.props))
    const component = createElement(Component, props)
    hydrate(component, root)
}
```

## Examples

For advanced use cases such as using client side routing, state management libraries, or different JavaScript view libraries altogether, check out the [examples](examples):

- [TypeScript](examples/typescript.md)
- [React with React Router](examples/react-with-react-router.md)
- [React with Redux](examples/react-with-redux.md)
- [Cycle.js](examples/cyclejs.md)
- [Cycle.js React](examples/cyclejs-react.md)
- [Vue.js](examples/vuejs.md)
