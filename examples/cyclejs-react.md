# [Cycle.js React](https://github.com/cyclejs/react) example

Install dependencies:

```bash
npm install react react-dom react-helmet @cycle/react @cycle/react-dom xstream 
```

Add a Django view:

```python
from django.shortcuts import render

def cycle_react_view(request):
    return render(request, 'template.js', context={
        'title': 'Django Cycle React SSR',
        'count': 0
    })
```

Export the root component converted to React component:

```javascript
import { Stream } from 'xstream'
import { h, makeComponent } from '@cycle/react'
import { h1, button, div, title } from '@cycle/react-dom'
import { Helmet } from 'react-helmet'

const main = sources => {
    const increments = sources.react.select('increment').events('click').mapTo(1)
    const decrements = sources.react.select('decrement').events('click').mapTo(-1)
    const counts = sources.react.props().map(props =>
        Stream.merge(increments, decrements).fold((acc, n) => acc + n, props.count)
    ).flatten()
    const views = Stream.combine(sources.react.props(), counts).map(([props, count]) =>
        div([
            h(Helmet, [
                title([props.title])
            ]),
            h1('Count ' + count),
            button({ sel: 'increment' }, '+'),
            button({ sel: 'decrement' }, '-'),
        ])
    )
    return {
        react: views
    }
}

export default makeComponent(main /*, drivers */)
```
