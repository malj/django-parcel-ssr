# [Cycle.js](https://cycle.js.org/) example

Install dependencies:

```bash
npm install xstream @cycle/run @cycle/dom @cycle/html
```

Create a `server.js` file in the project root:

```javascript
import { Stream } from 'xstream'
import { run } from '@cycle/run'
import { makeHTMLDriver } from '@cycle/html'
import { html, head, body, title, script, link, div } from '@cycle/dom'

export default Component => (bundle, props) => new Promise(resolve => {
    const serializedProps = encodeURIComponent(JSON.stringify(props))
    const main = sources => {
        const component = Component(sources)
        const views = Stream.combine(sources.props, component.DOM).map(([props, view]) =>
            html([
                head([
                    title([props.title]),
                    link({ attrs: { href: bundle.stylesheet, rel: 'stylesheet' } })
                ]),
                body([
                    div('#root', { attrs: { 'data-props': serializedProps } }, [
                        view
                    ]),
                    script({ attrs: { src: bundle.script } })
                ])
            ])
        )
        return {
            DOM: views
        }
    }
    const drivers = {
        DOM: makeHTMLDriver(html => {
            dispose()
            resolve('<!DOCTYPE html>' + html)
        }),
        props: () => Stream.of(props)
    }
    const dispose = run(main, drivers)
})
```

Create a `client.js` file in the project root:

```javascript
import { Stream } from 'xstream'
import { run } from '@cycle/run'
import { makeDOMDriver } from '@cycle/dom'

export default Component => {
    const container = document.getElementById('root')
    const props = JSON.parse(decodeURIComponent(container.dataset.props))
    const drivers = {
        DOM: makeDOMDriver(container),
        props: () => Stream.of(props)
    }
    run(Component, drivers)
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

Add a Django view and export the root component:

```python
from django.shortcuts import render

def cycle_view(request):
    return render(request, 'template.js', context={
        'title': 'Django Cycle SSR',
        'count': 0
    })
```

```javascript
import { Stream } from 'xstream'
import { h1, button, div } from '@cycle/dom'

export default sources => {
    const increments = sources.DOM.select('.increment').events('click').mapTo(1)
    const decrements = sources.DOM.select('.decrement').events('click').mapTo(-1)
    const counts = sources.props.map(props =>
        Stream.merge(increments, decrements).fold((acc, n) => acc + n, props.count)
    ).flatten()
    const views = counts.map(count =>
        div([
            h1('Count ' + count),
            button('.increment', '+'),
            button('.decrement', '-'),
        ])
    )
    return {
        DOM: views
    }
}
```
