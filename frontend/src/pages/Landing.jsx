import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import HeroSection from '../components/HeroSection';
import FeaturesSection from '../components/FeaturesSection';
import PricingSection from '../components/PricingSection';

export default function Landing() {
  return (
    <div className="min-h-screen bg-[#0d0d1a] text-white">
      <HeroSection />
      <FeaturesSection />
      <PricingSection />
    </div>
  );
}
