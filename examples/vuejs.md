# [Vue.js](https://vuejs.org/) example

Install dependencies:

```bash
npm install vue vue-server-renderer
```

Create a `server.js` file in the project root:

```javascript
import Vue from 'vue'
import { createRenderer } from 'vue-server-renderer'

export default Component => ({ script, stylesheet }, props) => {
    const serializedProps = encodeURIComponent(JSON.stringify(props))
    const component = new Vue({
        render: createElement => createElement(Component, { props })
    })
    return createRenderer().renderToString(component).then(html => `
        <!DOCTYPE html>
        <html>
            <head>
                <title>${props.title}</title>
                ${stylesheet && `<link href="${stylesheet}" rel="stylesheet">`}
            </head>
            <body>
                <div id="root" data-props="${serializedProps}">
                    ${html}
                    <script src="${script}"></script>
                </div>
            </body>
        </html>
    `)
}
```

Create a `client.js` file in the project root:

```javascript
import Vue from 'vue'

export default Component => {
    const root = document.getElementById('root')
    const props = JSON.parse(decodeURIComponent(root.dataset.props))
    const component = new Vue({
        render: createElement => createElement(Component, { props })
    })
    component.$mount(root)
}
```

Add custom scripts and `vue` extension to `settings.py`:

```python
'OPTIONS' : {
    'extensions': ['vue'],
    'scripts': {
        'server': os.path.join(BASE_DIR, 'server.js'),
        'client': os.path.join(BASE_DIR, 'client.js'),
    }
}
```

Add a Django view:

```python
from django.shortcuts import render

def vue_view(request):
    return render(request, 'template.vue', context={
        'title': 'Django Vue SSR',
        'initialCount': 0
    })
```

Export the root component from `template.vue`:

```vue
<template>
    <div>
        <h1>Count {{ count }}</h1>
        <button v-on:click="increment">+</button>
        <button v-on:click="decrement">-</button>
    </div>
</template>

<script>
export default {
    props: {
        initialCount: Number
    },
    data() {
        return {
            count: this.initialCount
        }
    },
    methods: {
        increment() {
            this.count++
        },
        decrement() {
            this.count--
        }
    }
}
</script>
```
