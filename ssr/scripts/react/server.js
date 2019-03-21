import React from 'react'
import ReactDOMServer from 'react-dom/server'
import { Helmet } from 'react-helmet'
import { flushToHTML } from 'styled-jsx/server'

export default Component => ({ script, stylesheet }, props) => {
    const component = React.createElement(Component, props)
    const html = ReactDOMServer.renderToString(component)
    const helmet = Helmet.renderStatic()
    const serializedProps = encodeURIComponent(JSON.stringify(props))

    return [
        '<!DOCTYPE html>',
        `<html ${helmet.htmlAttributes.toString()}>`,
        '<head>',
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width initial-scale=1.0"/>',
        helmet.title.toString(),
        helmet.base.toString(),
        helmet.meta.toString(),
        helmet.link.toString(),
        helmet.style.toString(),
        flushToHTML(),
        stylesheet && `<link href="${stylesheet}" rel="stylesheet">`,
        '</head>',
        `<body ${helmet.bodyAttributes.toString()}>`,
        helmet.noscript.toString(),
        `<div id="__react_root__" data-props="${serializedProps}">${html}</div>`,
        helmet.script.toString(),
        `<script src="${script}"></script>`,
        '</body>',
        '</html>'
    ].join('')
}
