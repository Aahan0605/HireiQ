import React from 'react';
import HeroSection from '../components/HeroSection';
import FeaturesSection from '../components/FeaturesSection';
import PricingSection from '../components/PricingSection';

export default function Landing() {
  return (
    <div className="relative min-h-screen">
      <HeroSection />
      <FeaturesSection />
      <PricingSection />
    </div>
  );
}
