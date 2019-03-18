const isProcessAlive = (pid) => {
    try {
        return process.kill(pid, 0)
    }
    catch (error) {
        return error.code === 'EPERM'
    }
}

export const link = (pid, interval) => setInterval(() => {
    if (!isProcessAlive(pid)) {
        process.exit()
    }
}, interval)

export const color = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    dim: '\x1b[2m',
    green: '\x1b[32m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m'
}
