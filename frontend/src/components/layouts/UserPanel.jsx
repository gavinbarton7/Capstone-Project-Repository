import { useEffect, useState } from 'react'

function UserPanel() {
    const [user, setUser] = useState(null)

    useEffect(() => {
        async function loadUser() {
            try {
                const response = await fetch('/api/auth/me', {
                    credentials: 'include'
                })

                if (response.ok) {
                    const data = await response.json()

                    // Handles either { user: {...} } or just {...}
                    setUser(data.user || data)
                }
            } catch (error) {
                console.error('Unable to load user:', error)
            }
        }

        loadUser()
    }, [])

    const firstName = user?.first_name || user?.firstName || ''
    const lastName = user?.last_name || user?.lastName || ''

    const fullName =
        `${firstName} ${lastName}`.trim() ||
        user?.name ||
        user?.email ||
        'User'

    const initials =
        firstName && lastName
            ? `${firstName[0]}${lastName[0]}`.toUpperCase()
            : fullName
                .split(' ')
                .map(word => word[0])
                .join('')
                .slice(0, 2)
                .toUpperCase()

    return (
        <aside className="user-panel">

            <div className="user-avatar">
                {initials}
            </div>

            <strong>{fullName}</strong>

            <span className="account-type">
                Personal account
            </span>

            <button className="account-selector">
                Owner account
            </button>

        </aside>
    )
}

export default UserPanel