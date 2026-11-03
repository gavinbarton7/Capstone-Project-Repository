import { NavLink } from 'react-router-dom'
import { Icon } from '@iconify/react'

function TopNavbar() {
    return (
        <nav className="top-navbar">

            <div className="brand">
                <div className="brand-icon">m</div>
                <span>Money</span>
            </div>

            <div className="main-navigation">

                <NavLink to="/dashboard">
                    <Icon icon="mdi:view-dashboard-outline" />
                    Dashboard
                </NavLink>

                <NavLink to="/accounts">
                    <Icon icon="mdi:bank-outline" />
                    Bank account
                </NavLink>

                <NavLink to="/investments">
                    <Icon icon="mdi:chart-line" />
                    Investment
                </NavLink>

                <NavLink to="/expenses">
                    <Icon icon="mdi:receipt-text-outline" />
                    Expenses
                </NavLink>

            </div>

            <div className="account-navigation">

                <NavLink to="/settings">
                    <Icon icon="mdi:cog-outline" />
                    Settings
                </NavLink>

                <NavLink to="/profile">
                    <Icon icon="mdi:account-outline" />
                    Profile
                </NavLink>

            </div>

        </nav>
    )
}

export default TopNavbar