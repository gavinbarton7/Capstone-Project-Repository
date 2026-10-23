import {
    BrowserRouter,
    Routes,
    Route,
    Navigate,
    Outlet
} from 'react-router-dom'

import TopNavbar from './components/navigation/TopNavbar'
import UserPanel from './components/layouts/UserPanel'

import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import BankAccounts from './pages/BankAccounts'
import Investments from './pages/Investments'
import Expenses from './pages/Expenses'
import Settings from './pages/Settings'
import Profile from './pages/Profile'

function MainLayout() {
    return (
        <>
            <TopNavbar />

            <div className="app-body">

                <UserPanel />

                <main className="main-content">
                    <Outlet />
                </main>

            </div>
        </>
    )
}

function App() {
    return (
        <BrowserRouter>

            <Routes>

                <Route
                    path="/"
                    element={<Navigate to="/login" replace />}
                />

                <Route
                    path="/login"
                    element={<Login />}
                />

                <Route
                    path="/register"
                    element={<Register />}
                />

                <Route element={<MainLayout />}>

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

                </Route>

                <Route
                    path="*"
                    element={<Navigate to="/login" replace />}
                />

            </Routes>

        </BrowserRouter>
    )
}

export default App