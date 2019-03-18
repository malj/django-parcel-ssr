const hydrate = require(process.env.SSR_HYDRATE).default
const Component = require(process.env.SSR_COMPONENT).default

hydrate(Component)
