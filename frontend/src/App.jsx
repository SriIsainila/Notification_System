import Footer from './components/Footer.jsx'
import Navbar from './components/Navbar.jsx'
import AppRoutes from './routes/AppRoutes.jsx'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-night text-ink">
      <Navbar />
      <main className="flex-1">
        <AppRoutes />
      </main>
      <Footer />
    </div>
  )
}
