import React, { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';

const DASH_PREFIXES = [
  '/dashboard', '/analyze', '/candidates', '/candidate',
  '/settings', '/jobs', '/bias-report', '/compare',
];

export default function ConstellationBackground() {
  const containerRef = useRef(null);
  const { pathname } = useLocation();
  const [vantaEffect, setVantaEffect] = useState(null);

  const isAuthPage = DASH_PREFIXES.some(p => pathname.startsWith(p));

  useEffect(() => {
    if (isAuthPage) return;

    let isMounted = true;
    let effect = null;

    const initVanta = () => {
      if (!containerRef.current || !window.VANTA || !window.VANTA.BIRDS) return;

      // Respect prefers-reduced-motion
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReducedMotion) return;

      try {
        effect = window.VANTA.BIRDS({
          el: containerRef.current,
          mouseControls: true,
          touchControls: true,
          gyroControls: false,
          minHeight: 200.00,
          minWidth: 200.00,
          scale: 1.00,
          scaleMobile: 1.00,
          birdSize: 1.50,
          wingSpan: 35.00,
          speedLimit: 10.00,
          separation: 68.00,
          alignment: 47.00,
          cohesion: 24.00,
          quantity: 3.00, // Balanced count so it feels premium and not cluttered
          backgroundAlpha: 0.00, // Transparent background to show theme gradients
          color1: 0x2dd4bf, // Theme Teal/Cyan
          color2: 0x8b5cf6, // Theme Violet/Purple
          colorMode: "variance"
        });
        if (isMounted) {
          setVantaEffect(effect);
        }
      } catch (err) {
        console.error("Error initializing Vanta Birds:", err);
      }
    };

    const loadScript = (src, globalKey) => {
      return new Promise((resolve) => {
        if (window[globalKey] || (globalKey === 'VANTA' && window.VANTA && window.VANTA.BIRDS)) {
          resolve();
          return;
        }

        const existing = document.querySelector(`script[src="${src}"]`);
        if (existing) {
          if (existing.dataset.loaded === 'true') {
            resolve();
          } else {
            existing.addEventListener('load', resolve);
          }
          return;
        }

        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        script.dataset.loaded = 'false';
        script.addEventListener('load', () => {
          script.dataset.loaded = 'true';
          resolve();
        });
        document.body.appendChild(script);
      });
    };

    // Load Three.js first, then Vanta Birds
    loadScript('https://cdnjs.cloudflare.com/ajax/libs/three.js/r134/three.min.js', 'THREE')
      .then(() => {
        if (!isMounted) return;
        return loadScript('https://cdn.jsdelivr.net/npm/vanta@latest/dist/vanta.birds.min.js', 'VANTA');
      })
      .then(() => {
        if (!isMounted) return;
        initVanta();
      });

    return () => {
      isMounted = false;
      if (effect) {
        effect.destroy();
      }
    };
  }, [isAuthPage]);

  if (isAuthPage) return null;

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 block w-full h-full z-0 opacity-40 pointer-events-none transition-opacity duration-1000"
    />
  );
}
