import os from 'os'
import cluster from 'cluster'
import http from 'http'
import url from 'url'
import { link, color } from './utils'

if (cluster.isMaster) {
    const WORKER_TTL = parseInt(process.env.WORKER_TTL)
    const DJANGO_PID = parseInt(process.env.DJANGO_PID)
    let interval = link(DJANGO_PID, WORKER_TTL)

    os.cpus().forEach((_, index) => {
        const worker = cluster.fork({ INDEX: index })
        worker.on('message', pid => {
            clearInterval(interval)
            interval = link(pid, WORKER_TTL)
        })
    })
    console.log(
        '🤓 ',
        `${color.bright}${color.blue}SSR master${color.reset}`,
        `${process.pid} spawned by`,
        '😎 ',
        `${color.bright}${color.green}Django client${color.reset}`,
        `${DJANGO_PID}`
    )
}
else {
    const SOCKET = process.env.SOCKET
    const SIGNAL = process.env.SIGNAL
    const INDEX = parseInt(process.env.INDEX)

    http.createServer(async (request, response) => {
        try {
            const { pathname, query } = url.parse(request.url, true)

            if (pathname === '/render') {
                const { default: render } = await import(query.bundle)
                const bundle = {
                    script: query.script,
                    stylesheet: query.stylesheet
                }
                const props = JSON.parse(query.props || null)
                const html = await render(bundle, props)

                response.end(html)
            }
            else {
                const pid = parseInt(query.pid)

                process.send(pid)
                response.end()
            }
        }
        catch (error) {
            response.statusCode = 500
            response.end(error.toString())
        }
    }).listen(SOCKET, () => {
        console.log(
            '🤖 ',
            `${color.bright}${color.cyan}SSR server${color.reset}`,
            `${process.pid} spawned at`,
            `${color.dim}${SOCKET}${color.reset}`
        )
        if (os.cpus().length === INDEX + 1) {
            console.log(SIGNAL)
            console.error(SIGNAL)
        }
    })
}
