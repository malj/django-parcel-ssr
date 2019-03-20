# React with [Redux](https://redux.js.org/) example

Install dependencies:

```bash
npm install redux react-redux
```

Create a `store.js` file in the project root:

```javascript
import { createStore } from 'redux'

const reducer = (state = 0, action) => {
    switch (action.type) {
        case 'INCREMENT':
            return state + 1
        case 'DECREMENT':
            return state - 1
        default:
            return state
    }
}

export default initialState => createStore(reducer, initialState)
```

Create a `server.js` file in the project root:

```javascript
import React from 'react'
import { Provider } from 'react-redux'
import createStore from './store'
import createRenderer from './.ssr/scripts/react/server'

export default Component => (bundle, props) => {
    const ComponentWithStore = props => (
        <Provider store={createStore(props.initialState)}>
            <Component {...props} />
        </Provider>
    )
    return createRenderer(ComponentWithStore)(bundle, props)
}
```

Create a `client.js` file in the project root:

```javascript
import React from 'react'
import { Provider } from 'react-redux'
import createStore from './store'
import hydrate from './.ssr/scripts/react/client'

export default Component => {
    const ComponentWithStore = props => (
        <Provider store={createStore(props.initialState)}>
            <Component {...props} />
        </Provider>
    )
    hydrate(ComponentWithStore)
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

Add optional initial state to context in your Django view:

```python
from django.shortcuts import render

def react_redux_view(request):
    return render(request, 'template.js', context={
        'initialState': 0
    })
```

Connect your root component with the Redux store:

```javascript
import React from 'react'
import { connect } from 'react-redux'

const mapStateToProps = state => ({
    count: state
})
const mapDispatchToProps = dispatch => ({
    increment: () => dispatch({ type: 'INCREMENT' }),
    decrement: () => dispatch({ type: 'DECREMENT' })
})
const Component = props => (
    <div>
        <h1>Count: {props.count}</h1>
        <button onClick={props.increment}>+</button>
        <button onClick={props.decrement}>-</button>
    </div>
)

export default connect(mapStateToProps, mapDispatchToProps)(Component)
```
