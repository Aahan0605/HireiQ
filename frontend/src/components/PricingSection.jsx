import React from 'react';
import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { useIntersection } from '../lib/hooks';
import { fadeUp, scaleIn } from '../lib/animations';

const PLANS = [
  {
    name: 'Starter',
    price: '$49',
    desc: 'For small HR teams making their first AI hires.',
    features: ['Up to 50 analyzes/mo', 'Basic GitHub parsing', 'Email support', 'PDF Export'],
    highlight: false,
  },
  {
    name: 'Pro',
    price: '$149',
    desc: 'Everything you need to scale your engineering team.',
    features: ['Unlimited analyzes', 'Deep code & social parsing', 'Priority 24/7 support', 'Team analytics dashboard', 'Custom scoring weights'],
    highlight: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    desc: 'For high-volume recruitment agencies and global tech firms.',
    features: ['Volume discounts', 'Dedicated account manager', 'API access', 'Custom integrations', 'SSO & advanced security'],
    highlight: false,
  }
];

export default function PricingSection() {
  const { ref, inView } = useIntersection(0.2);

  return (
    <section id="pricing" className="relative py-24 px-6 overflow-hidden">
      <div className="absolute top-0 right-[20%] -z-10 h-72 w-72 rounded-full bg-rose/10 opacity-40 blur-[100px]" />

      <div className="mx-auto max-w-6xl">
        <div className="mb-20 text-center">
          <h2 className="font-display text-4xl font-semibold tracking-tight text-white mb-4">
            Transparent Pricing
          </h2>
          <p className="text-text-2 text-lg">Scale your hiring without scaling your budget.</p>
        </div>

        <motion.div
          ref={ref}
          initial="initial"
          animate={inView ? "animate" : "initial"}
          className="mx-auto grid max-w-5xl gap-8 md:grid-cols-3 md:items-center"
        >
          {PLANS.map((plan, i) => (
            <motion.div
              key={i}
              variants={plan.highlight ? scaleIn : fadeUp}
              className={`relative rounded-3xl border p-8 backdrop-blur-md ${
                plan.highlight
                  ? 'border-mint bg-surface shadow-glow-mint md:-my-4 md:py-12'
                  : 'border-border bg-surface/50'
              }`}
            >
              {plan.highlight && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-mint px-4 py-1 text-sm font-semibold text-bg shadow-lg">
                  Most Popular
                </div>
              )}

              <h3 className="mb-2 text-2xl font-bold text-white">{plan.name}</h3>
              <p className="mb-6 h-12 text-sm text-text-2">{plan.desc}</p>
              
              <div className="mb-8 font-display text-4xl font-extrabold text-white">
                {plan.price}
                {plan.price !== 'Custom' && <span className="text-lg font-medium text-text-3">/mo</span>}
              </div>

              <button className={`mb-8 w-full rounded-full py-3 font-semibold transition-transform hover:scale-105 ${
                plan.highlight
                  ? 'bg-mint text-bg'
                  : 'bg-surface-3 text-white hover:bg-surface-2'
              }`}>
                {plan.price === 'Custom' ? 'Contact Sales' : 'Get Started'}
              </button>

              <ul className="space-y-4 text-sm text-text-1">
                {plan.features.map((feat, fIdx) => (
                  <li key={fIdx} className="flex items-center gap-3">
                    <Check className={`h-5 w-5 ${plan.highlight ? 'text-mint' : 'text-violet'}`} />
                    {feat}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
