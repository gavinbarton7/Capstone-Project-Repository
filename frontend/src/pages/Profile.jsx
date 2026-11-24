import { useEffect, useRef, useState } from 'react'

function Profile() {
    const fileInputRef = useRef(null)

    const [user, setUser] = useState(null)
    const [photo, setPhoto] = useState(null)
    const [savedMessage, setSavedMessage] = useState('')

    const [form, setForm] = useState({
        firstName: '',
        lastName: '',
        email: '',
        phone: '',
        birthday: '',
        street: '',
        city: '',
        state: '',
        zip: ''
    })

    useEffect(() => {
        async function loadUser() {
            try {
                const response = await fetch('/api/auth/me', {
                    credentials: 'include'
                })

                if (response.ok) {
                    const data = await response.json()
                    const currentUser = data.user || data

                    setUser(currentUser)

                    setForm(prev => ({
                        ...prev,
                        firstName:
                            currentUser.first_name ||
                            currentUser.firstName ||
                            '',
                        lastName:
                            currentUser.last_name ||
                            currentUser.lastName ||
                            '',
                        email: currentUser.email || ''
                    }))
                }
            } catch (error) {
                console.error('Unable to load profile:', error)
            }
        }

        loadUser()
    }, [])

    function handleChange(event) {
        const { name, value } = event.target

        setForm(prev => ({
            ...prev,
            [name]: value
        }))

        setSavedMessage('')
    }

    function handleCancel() {
        setForm(prev => ({
            ...prev,
            firstName:
                user?.first_name ||
                user?.firstName ||
                '',
            lastName:
                user?.last_name ||
                user?.lastName ||
                '',
            email: user?.email || ''
        }))

        setSavedMessage('')
    }

    function handleSave(event) {
        event.preventDefault()

        // Temporary frontend save until profile-update backend endpoint is added
        localStorage.setItem('money-profile', JSON.stringify(form))

        setSavedMessage('Profile saved')
    }

    function handlePhotoChange(event) {
        const file = event.target.files[0]

        if (file) {
            setPhoto(URL.createObjectURL(file))
        }
    }

    const initials =
        `${form.firstName?.[0] || ''}${form.lastName?.[0] || ''}`.toUpperCase() ||
        'U'

    const fullName =
        `${form.firstName} ${form.lastName}`.trim() ||
        form.email ||
        'User'

    return (
        <div className="profile-page">

            <div className="profile-banner">
                <div className="profile-banner-top" />

                <div className="profile-banner-content">

                    <div className="profile-large-avatar">
                        {photo ? (
                            <img src={photo} alt="Profile" />
                        ) : (
                            initials
                        )}
                    </div>

                    <div className="profile-banner-info">
                        <h1>{fullName}</h1>

                        <div className="profile-meta">
                            <span className="owner-badge">Owner</span>
                            <span>Personal account · Member since November 2026</span>
                        </div>
                    </div>

                    <button
                        className="change-photo-button"
                        onClick={() => fileInputRef.current?.click()}
                    >
                        Change photo
                    </button>

                    <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        hidden
                        onChange={handlePhotoChange}
                    />

                </div>
            </div>

            <form className="profile-details-card" onSubmit={handleSave}>

                <div className="profile-section-heading">
                    <h2>Personal details</h2>
                    <p>Used on statements and for verifying your identity.</p>
                </div>

                <div className="profile-form-grid">

                    <div className="profile-field">
                        <label>First name</label>
                        <input
                            name="firstName"
                            value={form.firstName}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="profile-field">
                        <label>Last name</label>
                        <input
                            name="lastName"
                            value={form.lastName}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="profile-field">
                        <label>Email</label>
                        <input
                            name="email"
                            type="email"
                            value={form.email}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="profile-field">
                        <label>Phone</label>
                        <input
                            name="phone"
                            placeholder="(000) 000-0000"
                            value={form.phone}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="profile-field">
                        <label>Birthday</label>
                        <input
                            name="birthday"
                            type="date"
                            value={form.birthday}
                            onChange={handleChange}
                        />
                    </div>

                </div>

                <div className="profile-divider" />

                <div className="profile-section-heading">
                    <h2>Address</h2>
                </div>

                <div className="profile-field profile-full-width">
                    <label>Street address</label>
                    <input
                        name="street"
                        placeholder="Street and number"
                        value={form.street}
                        onChange={handleChange}
                    />
                </div>

                <div className="profile-form-grid">

                    <div className="profile-field">
                        <label>City</label>
                        <input
                            name="city"
                            placeholder="City"
                            value={form.city}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="profile-field">
                        <label>State</label>
                        <input
                            name="state"
                            placeholder="State"
                            value={form.state}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="profile-field">
                        <label>ZIP code</label>
                        <input
                            name="zip"
                            placeholder="00000"
                            value={form.zip}
                            onChange={handleChange}
                        />
                    </div>

                </div>

                <div className="profile-actions">

                    {savedMessage && (
                        <span className="profile-saved-message">
                            {savedMessage}
                        </span>
                    )}

                    <button
                        type="button"
                        className="profile-cancel-button"
                        onClick={handleCancel}
                    >
                        Cancel
                    </button>

                    <button
                        type="submit"
                        className="profile-save-button"
                    >
                        Save profile
                    </button>

                </div>

            </form>

        </div>
    )
}

export default Profile