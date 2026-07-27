import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { addTrackedProduct } from '../services/productService.js'

export default function AddProduct() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    url: '',
    changeScope: 'all',
    notifyChannel: 'email',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    try {
      new URL(form.url)
    } catch {
      setError('Please paste a valid product URL.')
      return
    }

    setLoading(true)
    try {
      await addTrackedProduct(form)
      navigate('/dashboard')
    } catch (err) {
      setError(err.message || 'Could not add this product. Try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto px-6 py-16">
      <h1 className="font-display text-3xl font-bold mb-2">Track a new product</h1>
      <p className="text-muted mb-8 text-sm">
        Paste the product link and choose which changes you want to follow.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm text-muted mb-1.5">
            Product URL
          </label>
          <input
            id="url"
            type="url"
            required
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
            className="w-full bg-night-surface border border-ink/15 rounded-lg px-4 py-2.5 focus-ring outline-none"
            placeholder="https://www.daraz.lk/products/..."
          />
        </div>

        <div>
          <label htmlFor="changeScope" className="block text-sm text-muted mb-1.5">
            Changes to track
          </label>
          <select
            id="changeScope"
            value={form.changeScope}
            onChange={(e) => setForm({ ...form, changeScope: e.target.value })}
            className="w-full bg-night-surface border border-ink/15 rounded-lg px-4 py-2.5 focus-ring outline-none"
          >
            <option value="price">Price changes</option>
            <option value="stock">Stock changes</option>
            <option value="all">All changes</option>
          </select>
          <p className="text-xs text-muted mt-1.5">
            You will be notified when the selected product information changes.
          </p>
        </div>

        <div>
          <label htmlFor="notifyChannel" className="block text-sm text-muted mb-1.5">
            Notify me via
          </label>
          <select
            id="notifyChannel"
            value={form.notifyChannel}
            onChange={(e) => setForm({ ...form, notifyChannel: e.target.value })}
            className="w-full bg-night-surface border border-ink/15 rounded-lg px-4 py-2.5 focus-ring outline-none"
          >
            <option value="email">In e-mail</option>
            <option value="system">System</option>
          </select>
        </div>

        {error && <p className="text-coral text-sm">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gold text-night font-semibold py-2.5 rounded-full hover:bg-gold-soft transition-colors focus-ring disabled:opacity-60"
        >
          {loading ? 'Adding…' : 'Start tracking'}
        </button>
      </form>
    </div>
  )
}
