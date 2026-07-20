import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import ProductCard from '../components/ProductCard.jsx'
import { useAuth } from '../context/AuthContext.jsx'
import { getTrackedProducts, deleteTrackedItem } from '../api/products.js'

// Placeholder data so the dashboard is visible before the backend is connected.
// Once /api/products is live, this is replaced by the real fetch below.
const MOCK_PRODUCTS = [
  {
    id: '1',
    name: 'Noise Cancelling Headphones',
    store_name: 'Daraz.lk',
    current_price: 8490,
    target_price: 9000,
    image_url: '',
    url: '#',
    in_stock: true,
  },
  {
    id: '2',
    name: 'Mechanical Keyboard 87-Key',
    store_name: 'Amazon.in',
    current_price: 12500,
    target_price: 10000,
    image_url: '',
    url: '#',
    in_stock: true,
  },
]

export default function Dashboard() {
  const { token } = useAuth()
  const [products, setProducts] = useState(MOCK_PRODUCTS)
  const [loading, setLoading] = useState(true)
  const [usingMock, setUsingMock] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const data = await getTrackedProducts(token)
        setProducts(data)
        setUsingMock(false)
      } catch {
        // Backend not connected yet — keep showing mock data
        setUsingMock(true)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [token])

  async function handleDelete(id) {
    setProducts((prev) => prev.filter((p) => p.id !== id))
    if (!usingMock) {
      try {
        await deleteTrackedItem(id, token)
      } catch {
        // silently ignore for now — could add a toast here
      }
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl font-bold">Your tracked products</h1>
          <p className="text-muted text-sm mt-1">
            {usingMock ? 'Showing sample data — connect your backend to see real prices.' : `${products.length} product(s) tracked`}
          </p>
        </div>
        <Link
          to="/add-product"
          className="flex items-center gap-1.5 bg-gold text-night text-sm font-semibold px-4 py-2.5 rounded-full hover:bg-gold-soft transition-colors focus-ring flex-shrink-0"
        >
          <Plus size={16} strokeWidth={2.5} />
          Track a product
        </Link>
      </div>

      {loading ? (
        <p className="text-muted text-sm">Loading…</p>
      ) : products.length === 0 ? (
        <div className="text-center py-20 border border-dashed border-white/15 rounded-2xl">
          <p className="text-muted mb-4">You're not tracking anything yet.</p>
          <Link to="/add-product" className="text-gold hover:text-gold-soft font-medium focus-ring rounded">
            Add your first product →
          </Link>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 gap-4">
          {products.map((p) => (
            <ProductCard key={p.id} product={p} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  )
}
