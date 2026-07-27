import { Link } from 'react-router-dom'
import { CheckCircle2, Clock3, History, Link2, MailCheck, ScanEye } from 'lucide-react'

const steps = [
  {
    icon: Link2,
    title: 'Paste the product link',
    desc: 'Copy any product URL from Daraz, Amazon, or your favourite store and drop it in.',
  },
  {
    icon: ScanEye,
    title: 'We watch it for you',
    desc: 'Nilify checks the price and stock status on a schedule, quietly, in the background.',
  },
  {
    icon: MailCheck,
    title: 'Get notified when it changes',
    desc: 'An e-mail or system alert arrives when your selected product information changes.',
  },
]

export default function Landing() {
  return (
    <div>
      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-20 pb-24 grid md:grid-cols-2 gap-12 items-center">
        <div>
          <p className="inline-block text-xs font-semibold tracking-widest uppercase text-gold bg-gold/10 px-3 py-1 rounded-full mb-6">
            Never overpay again
          </p>
          <h1 className="font-display text-5xl md:text-6xl font-extrabold leading-[1.05] mb-6">
            Watch prices.
            <br />
            <span className="text-gold">Not screens.</span>
          </h1>
          <p className="text-muted text-lg mb-8 max-w-md">
            Paste any product link and Nilify tells you the moment the price drops
            or it's back in stock — so you never have to check manually again.
          </p>
          <div className="flex gap-3">
            <Link
              to="/register"
              className="bg-gold text-night font-semibold px-6 py-3 rounded-full hover:bg-gold-soft transition-colors focus-ring"
            >
              Start tracking, free
            </Link>
            <a
              href="#how-it-works"
              className="border border-ink/20 px-6 py-3 rounded-full hover:border-gold transition-colors focus-ring"
            >
              See how it works
            </a>
          </div>
        </div>

        <div className="bg-night-surface border border-ink/10 shadow-sm rounded-2xl p-6">
          <div className="flex items-center justify-between gap-4 mb-5">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted mb-1">URL check history</p>
              <h3 className="font-medium">daraz.lk/products/...</h3>
            </div>
            <History size={22} className="text-gold flex-shrink-0" />
          </div>

          <div className="relative ml-2 space-y-5 before:absolute before:left-[7px] before:top-3 before:bottom-3 before:w-px before:bg-gold/25">
            <div className="relative flex items-start gap-3">
              <span className="relative z-10 mt-1 w-4 h-4 rounded-full bg-gold flex items-center justify-center">
                <CheckCircle2 size={11} className="text-white" />
              </span>
              <div>
                <p className="text-sm font-medium">URL added for tracking</p>
                <p className="text-xs text-muted">Today, 9:00 AM</p>
              </div>
            </div>
            <div className="relative flex items-start gap-3">
              <span className="relative z-10 mt-1 w-4 h-4 rounded-full bg-gold flex items-center justify-center">
                <ScanEye size={10} className="text-white" />
              </span>
              <div>
                <p className="text-sm font-medium">Product URL checked</p>
                <p className="text-xs text-muted">Today, 9:05 AM</p>
              </div>
            </div>
            <div className="relative flex items-start gap-3">
              <span className="relative z-10 mt-1 w-4 h-4 rounded-full bg-night-surface-2 border border-gold/30 flex items-center justify-center">
                <Clock3 size={10} className="text-gold" />
              </span>
              <div>
                <p className="text-sm font-medium">Next check scheduled</p>
                <p className="text-xs text-muted">Today, 9:10 AM</p>
              </div>
            </div>
          </div>

          <Link
            to="/dashboard"
            className="inline-flex mt-5 text-sm font-semibold text-gold hover:text-gold-soft focus-ring rounded"
          >
            View tracked URL history →
          </Link>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="max-w-6xl mx-auto px-6 py-20 border-t border-ink/10">
        <h2 className="font-display text-3xl font-bold mb-2">How it works</h2>
        <p className="text-muted mb-12">Three steps, then Nilify does the watching.</p>

        <div className="grid md:grid-cols-3 gap-8">
          {steps.map(({ icon: Icon, title, desc }) => (
            <div key={title}>
              <div className="w-11 h-11 rounded-xl bg-night-surface border border-ink/10 shadow-sm flex items-center justify-center mb-4">
                <Icon size={20} className="text-gold" />
              </div>
              <h3 className="font-display font-semibold text-lg mb-2">{title}</h3>
              <p className="text-muted text-sm leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-20 border-t border-ink/10 text-center">
        <h2 className="font-display text-3xl font-bold mb-4">Ready to stop checking prices by hand?</h2>
        <Link
          to="/register"
          className="inline-block bg-gold text-night font-semibold px-8 py-3 rounded-full hover:bg-gold-soft transition-colors focus-ring"
        >
          Create your free account
        </Link>
      </section>
    </div>
  )
}
