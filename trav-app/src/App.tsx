import { HashRouter, Routes, Route, NavLink } from 'react-router-dom'
import { HomePage } from './pages/HomePage'
import { TrackPage } from './pages/TrackPage'
import { CalendarPage } from './pages/CalendarPage'
import { NearbyPage } from './pages/NearbyPage'

export default function App() {
  return (
    <HashRouter>
      <div className="app">
        <header className="app-header">
          <h1>🏇 Hitta travbanan</h1>
          <nav className="app-nav">
            <NavLink to="/" end>
              Karta
            </NavLink>
            <NavLink to="/kalender">Kalender</NavLink>
            <NavLink to="/nara-dig">Nära dig</NavLink>
          </nav>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/bana/:trackId" element={<TrackPage />} />
            <Route path="/kalender" element={<CalendarPage />} />
            <Route path="/nara-dig" element={<NearbyPage />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  )
}
