import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { loginUser } from '../api'

function Login() {
    const [showPassword, setShowPassword] = useState(false)

    const [error, setError] = useState('')
    const [submitting, setSubmitting] = useState(false)

    const navigate = useNavigate()
    const location = useLocation()

    // Set by the Register page after an account is created.
    const justRegistered = location.state?.registered === true

    async function handleSubmit(event) {
        event.preventDefault()

        const form = new FormData(event.currentTarget)

        setError('')
        setSubmitting(true)

        try {
            await loginUser({
                email: form.get('email'),
                password: form.get('password'),
                rememberMe: form.get('rememberMe') === 'on',
            })

            navigate('/dashboard')
        } catch (err) {
            setError(err.message)
            setSubmitting(false)
        }
    }

    return (
        <div className="auth-page">

            <div className="auth-shell">

                <div className="auth-brand">
                    <div className="brand-icon">m</div>
                    <span>Money</span>
                </div>

                <div className="auth-card">

                    <h1>Sign in to Money</h1>

                    <p className="auth-subtitle">
                        Use the email you registered with.
                    </p>

                    {justRegistered && !error && (
                        <div className="alert alert-success" role="status">
                            Account created. Sign in to continue.
                        </div>
                    )}

                    {error && (
                        <div className="alert alert-danger" role="alert">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>

                        <div className="mb-3">
                            <label
                                htmlFor="login-email"
                                className="form-label"
                            >
                                Email
                            </label>

                            <input
                                id="login-email"
                                name="email"
                                type="email"
                                autoComplete="email"
                                className="form-control"
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        <div className="mb-3">
                            <label
                                htmlFor="login-password"
                                className="form-label"
                            >
                                Password
                            </label>

                            <div className="password-field">

                                <input
                                    id="login-password"
                                    name="password"
                                    autoComplete="current-password"
                                    type={showPassword ? 'text' : 'password'}
                                    className="form-control"
                                    placeholder="Your password"
                                    required
                                />

                                <button
                                    type="button"
                                    className="password-toggle"
                                    onClick={() => setShowPassword(!showPassword)}
                                >
                                    {showPassword ? 'Hide' : 'Show'}
                                </button>

                            </div>
                        </div>

                        <div className="form-check mb-4">

                            <input
                                id="remember-me"
                                name="rememberMe"
                                type="checkbox"
                                className="form-check-input"
                            />

                            <label
                                htmlFor="remember-me"
                                className="form-check-label"
                            >
                                Keep me signed in on this device
                            </label>

                        </div>

                        <button
                            type="submit"
                            className="btn auth-primary-button w-100"
                            disabled={submitting}
                        >
                            {submitting ? 'Signing in…' : 'Sign in'}
                        </button>

                    </form>

                    <p className="auth-switch">
                        Don't have an account?{' '}
                        <Link to="/register">
                            Create one
                        </Link>
                    </p>

                </div>

            </div>

        </div>
    )
}

export default Login