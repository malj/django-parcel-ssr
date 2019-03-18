import React from 'react'
import ReactDOM from 'react-dom'

export default Component => {
    const container = document.getElementById('__react_root__')
    const meta = document.querySelector('meta[name="__react_props__"]')
    const serializedProps = meta.getAttribute('content')
    const props = JSON.parse(decodeURIComponent(serializedProps))
    const component = React.createElement(Component, props)

    ReactDOM.hydrate(component, container)
}
