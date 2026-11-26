import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Settings() {
    const navigate = useNavigate()
    const [activeTab, setActiveTab] = useState('general')

    const [settings, setSettings] = useState(() => {
        const saved = localStorage.getItem('money-settings')

        return saved
            ? JSON.parse(saved)
            : {
                language: 'English (US)',
                dateFormat: 'MM/DD/YYYY',
                weekStartsOn: 'Sunday',
                emailNotifications: true,
                budgetAlerts: true
            }
    })

    useEffect(() => {
        localStorage.setItem('money-settings', JSON.stringify(settings))
    }, [settings])

    function updateSetting(name, value) {
        setSettings(prev => ({
            ...prev,
            [name]: value
        }))
    }

    async function handleLogout() {
        try {
            const response = await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include'
            })

            if (response.ok) {
                navigate('/login')
            } else {
                console.error('Logout failed')
            }
        } catch (error) {
            console.error('Unable to log out:', error)
        }
    }

    return (
        <div className="settings-page">

            <div className="settings-heading">
                <h1>Settings</h1>
                <p>Manage preferences and alerts for your workspace.</p>
            </div>

            <div className="settings-tabs">

                <button
                    className={activeTab === 'general' ? 'active' : ''}
                    onClick={() => setActiveTab('general')}
                >
                    General
                </button>

                <button
                    className={activeTab === 'notifications' ? 'active' : ''}
                    onClick={() => setActiveTab('notifications')}
                >
                    Notification
                </button>

                <button
                    className={activeTab === 'bank' ? 'active' : ''}
                    onClick={() => setActiveTab('bank')}
                >
                    Connected bank
                </button>

            </div>

            {activeTab === 'general' && (
                <div className="settings-panel">

                    <h2>Preferences</h2>

                    <p className="settings-description">
                        Manage how dates and other information appear across Money.
                    </p>

                    <div className="settings-grid">

                        <div className="settings-field">
                            <label>Language</label>

                            <select
                                value={settings.language}
                                onChange={e =>
                                    updateSetting('language', e.target.value)
                                }
                            >
                                <option>English (US)</option>
                                <option>English (UK)</option>
                            </select>
                        </div>

                        <div className="settings-field">
                            <label>Date format</label>

                            <select
                                value={settings.dateFormat}
                                onChange={e =>
                                    updateSetting('dateFormat', e.target.value)
                                }
                            >
                                <option>MM/DD/YYYY</option>
                                <option>DD/MM/YYYY</option>
                                <option>YYYY-MM-DD</option>
                            </select>
                        </div>

                        <div className="settings-field">
                            <label>Week starts on</label>

                            <select
                                value={settings.weekStartsOn}
                                onChange={e =>
                                    updateSetting('weekStartsOn', e.target.value)
                                }
                            >
                                <option>Sunday</option>
                                <option>Monday</option>
                            </select>
                        </div>

                    </div>

                    <div className="settings-option-row">

                        <div>
                            <strong>Log out</strong>
                            <p>
                                Sign out of your Money account on this device.
                            </p>
                        </div>

                        <button
                            className="settings-logout-button"
                            onClick={handleLogout}
                        >
                            Log out
                        </button>

                    </div>

                </div>
            )}

            {activeTab === 'notifications' && (
                <div className="settings-panel">

                    <h2>Notifications</h2>

                    <p className="settings-description">
                        Choose which alerts you want to receive.
                    </p>

                    <div className="settings-option-row">

                        <div>
                            <strong>Email notifications</strong>
                            <p>
                                Receive important account updates by email.
                            </p>
                        </div>

                        <input
                            type="checkbox"
                            checked={settings.emailNotifications}
                            onChange={e =>
                                updateSetting(
                                    'emailNotifications',
                                    e.target.checked
                                )
                            }
                        />

                    </div>

                    <div className="settings-option-row">

                        <div>
                            <strong>Budget alerts</strong>
                            <p>
                                Get notified when you are close to a budget limit.
                            </p>
                        </div>

                        <input
                            type="checkbox"
                            checked={settings.budgetAlerts}
                            onChange={e =>
                                updateSetting(
                                    'budgetAlerts',
                                    e.target.checked
                                )
                            }
                        />

                    </div>

                </div>
            )}

            {activeTab === 'bank' && (
                <div className="settings-panel">

                    <h2>Connected bank</h2>

                    <p className="settings-description">
                        Manage financial accounts connected to Money.
                    </p>

                    <div className="settings-option-row">

                        <div>
                            <strong>Bank accounts</strong>
                            <p>
                                View or connect your supported financial accounts.
                            </p>
                        </div>

                        <button
                            className="settings-green-button"
                            onClick={() => navigate('/accounts')}
                        >
                            Manage accounts
                        </button>

                    </div>

                </div>
            )}

        </div>
    )
}

export default Settings