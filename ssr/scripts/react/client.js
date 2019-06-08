import React from 'react'
import ReactDOM from 'react-dom'

export default Component => {
    const container = document.getElementById('__react_root__')
    const props = JSON.parse(decodeURIComponent(container.dataset.props))
    const component = React.createElement(Component, props)

    ReactDOM[process.env.NODE_ENV === 'production'
        ? 'hydrate'
        : 'render'
    ](component, container)
}
