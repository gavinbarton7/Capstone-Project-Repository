import {
    BrowserRouter,
    Routes,
    Route,
    Navigate
} from 'react-router-dom'

import TopNavbar from './components/navigation/TopNavbar'
import UserPanel from './components/layouts/UserPanel'

import Dashboard from './pages/Dashboard'
import BankAccounts from './pages/BankAccounts'
import Investments from './pages/Investments'
import Expenses from './pages/Expenses'
import Settings from './pages/Settings'
import Profile from './pages/Profile'

function App() {
    return (
        <BrowserRouter>

            <TopNavbar />

            <div className="app-body">

                <UserPanel />

                <main className="main-content">

                    <Routes>

                        <Route
                            path="/"
                            element={<Navigate to="/dashboard" replace />}
                        />

                        <Route
                            path="/dashboard"
                            element={<Dashboard />}
                        />

                        <Route
                            path="/accounts"
                            element={<BankAccounts />}
                        />

                        <Route
                            path="/investments"
                            element={<Investments />}
                        />

                        <Route
                            path="/expenses"
                            element={<Expenses />}
                        />

                        <Route
                            path="/settings"
                            element={<Settings />}
                        />

                        <Route
                            path="/profile"
                            element={<Profile />}
                        />

                    </Routes>

                </main>

            </div>

        </BrowserRouter>
    )
}

export default App