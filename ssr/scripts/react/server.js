import React from 'react'
import ReactDOMServer from 'react-dom/server'
import { Helmet } from 'react-helmet'

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
        `<meta name="__react_props__" content="${serializedProps}">`,
        helmet.meta.toString(),
        helmet.link.toString(),
        helmet.style.toString(),
        stylesheet && `<link href="${stylesheet}" rel="stylesheet">`,
        '</head>',
        `<body ${helmet.bodyAttributes.toString()}>`,
        helmet.noscript.toString(),
        `<div id="__react_root__">${html}</div>`,
        helmet.script.toString(),
        `<script src="${script}"></script>`,
        '</body>',
        '</html>'
    ].join('')
}
