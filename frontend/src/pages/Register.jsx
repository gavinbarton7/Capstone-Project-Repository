import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

function Register() {
    const [showPassword, setShowPassword] = useState(false)

    const navigate = useNavigate()

    function handleSubmit(event) {
        event.preventDefault()

        // Temporary prototype behavior.
        // Account creation will connect to the backend later.
        navigate('/login')
    }

    return (
        <div className="auth-page">

            <div className="auth-shell">

                <div className="auth-brand">
                    <div className="brand-icon">m</div>
                    <span>Money</span>
                </div>

                <div className="auth-card">

                    <h1>Create your account</h1>

                    <p className="auth-subtitle">
                        Create your account to start managing your finances.
                    </p>

                    <form onSubmit={handleSubmit}>

                        <div className="row">

                            <div className="col-md-6 mb-3">
                                <label
                                    htmlFor="first-name"
                                    className="form-label"
                                >
                                    First name
                                </label>

                                <input
                                    id="first-name"
                                    type="text"
                                    className="form-control"
                                    placeholder="Alex"
                                    required
                                />
                            </div>

                            <div className="col-md-6 mb-3">
                                <label
                                    htmlFor="last-name"
                                    className="form-label"
                                >
                                    Last name
                                </label>

                                <input
                                    id="last-name"
                                    type="text"
                                    className="form-control"
                                    placeholder="Lee"
                                    required
                                />
                            </div>

                        </div>

                        <div className="mb-3">
                            <label
                                htmlFor="register-email"
                                className="form-label"
                            >
                                Email
                            </label>

                            <input
                                id="register-email"
                                type="email"
                                className="form-control"
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        <div className="mb-4">

                            <label
                                htmlFor="register-password"
                                className="form-label"
                            >
                                Password
                            </label>

                            <div className="password-field">

                                <input
                                    id="register-password"
                                    type={showPassword ? 'text' : 'password'}
                                    className="form-control"
                                    placeholder="At least 8 characters"
                                    minLength="8"
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

                            <div className="form-text">
                                Use at least 8 characters.
                            </div>

                        </div>

                        <button
                            type="submit"
                            className="btn auth-primary-button w-100"
                        >
                            Create account
                        </button>

                    </form>

                    <p className="auth-switch">
                        Already have an account?{' '}
                        <Link to="/login">
                            Sign in
                        </Link>
                    </p>

                </div>

            </div>

        </div>
    )
}

export default Register