const createRenderer = require(process.env.SCRIPT).default
const Component = require(process.env.COMPONENT).default

module.exports = createRenderer(Component)
