import { useEffect, useState } from 'react'
import { Navigate, Outlet } from 'react-router-dom'

function ProtectedRoute() {
    const [isAuthenticated, setIsAuthenticated] = useState(null)

    useEffect(() => {
        async function checkUser() {
            try {
                const response = await fetch('/api/auth/me', {
                    credentials: 'include'
                })

                setIsAuthenticated(response.ok)
            } catch (error) {
                console.error('Unable to check login status:', error)
                setIsAuthenticated(false)
            }
        }

        checkUser()
    }, [])

    if (isAuthenticated === null) {
        return <div>Loading...</div>
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />
    }

    return <Outlet />
}

export default ProtectedRoute