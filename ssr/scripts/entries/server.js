const createRenderer = require(process.env.SSR_CREATE_RENDERER).default
const Component = require(process.env.SSR_COMPONENT).default

module.exports = createRenderer(Component)
