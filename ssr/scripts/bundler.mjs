import Bundler from 'parcel-bundler'
import http from 'http'
import url from 'url'
import { link, color } from './utils'

const { entry, config } = JSON.parse(process.env.PARCEL_OPTIONS)
const bundler = new Bundler(entry, config)

if (!config.watch) {
    bundler.bundle().catch(console.error)
}
else {
    const SIGNAL = process.env.SIGNAL
    const SOCKET = process.env.SOCKET
    const WORKER_TTL = parseInt(process.env.WORKER_TTL)
    const DJANGO_PID = parseInt(process.env.DJANGO_PID)
    let interval = link(DJANGO_PID, WORKER_TTL)
    let buffer = ''

    http.createServer((request, response) => {
        const { query } = url.parse(request.url, true)
        const pid = parseInt(query.pid)

        clearInterval(interval)
        interval = link(pid, WORKER_TTL)

        response.end(buffer)
        buffer = ''

    }).listen(SOCKET, async () => {
        console.log(
            '🤠 ',
            `${color.bright}${color.magenta}SSR worker${color.reset}`,
            `${process.pid} spawned at`,
            `${color.dim}${SOCKET}${color.reset}`
        )
        try {
            await bundler.bundle()
        }
        catch (error) {
            console.error(error)
        }
        console.log(SIGNAL)
        console.error(SIGNAL)
        process.stdout.write = (write => (stdout, ...args) => {
            buffer += stdout
            write.apply(process.stdout, [stdout, ...args])
        })(process.stdout.write)
    })
}
