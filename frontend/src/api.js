// Small wrapper around fetch for talking to the backend.
// Requests go to /api/..., which the Vite dev server forwards to the Python
// API (see vite.config.js).

async function request(method, path, body) {
    let response

    try {
        response = await fetch(`/api${path}`, {
            method,
            headers: body ? { 'Content-Type': 'application/json' } : undefined,
            body: body ? JSON.stringify(body) : undefined,
            credentials: 'same-origin', // send the session cookie
        })
    } catch {
        throw new Error('Cannot reach the server. Is the backend running?')
    }

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
        throw new Error(data.error || 'Something went wrong. Please try again.')
    }

    return data
}

export function registerUser({ firstName, lastName, email, password }) {
    return request('POST', '/auth/register', {
        first_name: firstName,
        last_name: lastName,
        email,
        password,
    })
}

export function loginUser({ email, password, rememberMe }) {
    return request('POST', '/auth/login', {
        email,
        password,
        remember_me: rememberMe,
    })
}

export function logoutUser() {
    return request('POST', '/auth/logout')
}

export function getCurrentUser() {
    return request('GET', '/auth/me')
}
