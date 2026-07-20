import { Trash2, ExternalLink, TrendingDown } from 'lucide-react'

export default function ProductCard({ product, onDelete }) {
  const {
    name,
    image_url,
    current_price,
    target_price,
    store_name,
    url,
    in_stock = true,
  } = product

  const isBelowTarget = target_price && current_price <= target_price

  return (
    <div className="price-tag bg-night-surface border border-white/10 flex gap-4 p-4 pr-5">
      <img
        src={image_url || 'https://placehold.co/96x96/262550/9C9AC0?text=No+Image'}
        alt={name}
        className="w-20 h-20 rounded-lg object-cover flex-shrink-0 bg-night-surface-2"
      />

      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-xs uppercase tracking-wide text-muted mb-0.5">{store_name}</p>
            <h3 className="font-medium truncate pr-2">{name}</h3>
          </div>
          <button
            onClick={() => onDelete?.(product.id)}
            aria-label="Stop tracking this product"
            className="text-muted hover:text-coral transition-colors focus-ring rounded flex-shrink-0"
          >
            <Trash2 size={16} />
          </button>
        </div>

        <div className="flex items-center gap-3 mt-2">
          <span className="font-display font-bold text-lg">
            Rs. {Number(current_price).toLocaleString()}
          </span>
          {target_price && (
            <span className="text-xs text-muted">target Rs. {Number(target_price).toLocaleString()}</span>
          )}
          {isBelowTarget && (
            <span className="flex items-center gap-1 text-xs font-medium text-mint bg-mint/10 px-2 py-0.5 rounded-full">
              <TrendingDown size={12} /> Below target
            </span>
          )}
          {!in_stock && (
            <span className="text-xs font-medium text-coral bg-coral/10 px-2 py-0.5 rounded-full">
              Out of stock
            </span>
          )}
        </div>

        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1 text-xs text-gold hover:text-gold-soft mt-2 focus-ring rounded"
        >
          View product <ExternalLink size={12} />
        </a>
      </div>
    </div>
  )
}
