# React with [React Router](https://reacttraining.com/react-router/web/) example

Install dependencies:

```bash
npm install react-router-dom
```

Create a `server.js` file in the project root:

```javascript
import React from 'react'
import { StaticRouter } from 'react-router-dom'
import createRenderer from './.ssr/scripts/react/server'

export default Component => (bundle, props) => {
    const ComponentWithRouter = props => (
        <StaticRouter location={props.path}>
            <Component {...props} />
        </StaticRouter>
    )
    return createRenderer(ComponentWithRouter)(bundle, props)
}
```

Create a `client.js` file in the project root:

```javascript
import React from 'react'
import { BrowserRouter } from 'react-router-dom'
import hydrate from './.ssr/scripts/react/client'

export default Component => {
    const ComponentWithRouter = props => (
        <BrowserRouter>
            <Component {...props} />
        </BrowserRouter>
    )
    hydrate(ComponentWithRouter)
}
```

Add custom scripts to `settings.py`:

```python
'OPTIONS' : {
    'scripts': {
        'server': os.path.join(BASE_DIR, 'server.js'),
        'client': os.path.join(BASE_DIR, 'client.js'),
    }
}
```

In your `urls.py` add the request path to context in your Django view and and assign the view to all routes used by React Router:

```python
from django.urls import re_path
from django.shortcuts import render

def react_router_view(request, *args, **kwargs):
    return render(request, 'template.js', context={
        'path': request.path
    })
    
urlpatterns = [
    # ...
    re_path(r'^((foo|bar)/)?$', react_router_view)
]

```

Export your root component with the same routes:

```javascript
import React from 'react'
import { Helmet } from 'react-helmet'
import { Route, Switch, Link } from 'react-router-dom'

export default () => (
    <div>
        <ul>
            <li><Link to="/">Home</Link></li>
            <li><Link to="/foo/">Foo</Link></li>
            <li><Link to="/bar/">Bar</Link></li>
        </ul>

        <Switch>
            <Route exact path="/" render={() => <Page title="Home" />} />
            <Route path="/foo/" render={() => <Page title="Foo" />} />
            <Route path="/bar/" render={() => <Page title="Bar" />} />
        </Switch>
    </div>
)

const Page = props => (
    <div>
        <Helmet>
            <title>{props.title}</title>
        </Helmet>

        <h1>Hello from {props.title}</h1>
    </div>
)
```
