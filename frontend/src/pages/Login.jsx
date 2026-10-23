import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

function Login() {
    const [showPassword, setShowPassword] = useState(false)

    const navigate = useNavigate()

    function handleSubmit(event) {
        event.preventDefault()

        // Temporary prototype behavior.
        // Backend authentication will be added later.
        navigate('/dashboard')
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
                                type="email"
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
                        >
                            Sign in
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