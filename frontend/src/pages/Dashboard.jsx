import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import ProductCard from '../components/ProductCard.jsx'
import { deleteTrackedItem, getTrackedProducts } from '../services/productService.js'

export default function Dashboard() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        const data = await getTrackedProducts()
        setProducts(data)
      } catch (err) {
        setError(err.message || 'Could not load tracked products.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleDelete(id) {
    setError('')
    try {
      await deleteTrackedItem(id)
      setProducts((previous) => previous.filter((product) => product.id !== id))
    } catch (err) {
      setError(err.message || 'Could not remove this product.')
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl font-bold">Your tracked products</h1>
          <p className="text-muted text-sm mt-1">
            {`${products.length} product(s) tracked`}
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

      {error && <p className="text-coral text-sm mb-4">{error}</p>}

      {loading ? (
        <p className="text-muted text-sm">Loading…</p>
      ) : products.length === 0 ? (
        <div className="text-center py-20 border border-dashed border-ink/20 rounded-2xl bg-white/50">
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
