import { useEffect, useRef, useState } from 'react';
import { CountUp } from 'countup.js';
import { useInView } from 'react-intersection-observer';
import { useScroll, useTransform } from 'framer-motion';

export function useMagneticTilt(maxTilt = 8) {
  const ref = useRef(null);

  const handleMouseMove = (e) => {
    const prefersMotion = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (!prefersMotion || !ref.current) return;
    
    // Disable on touch devices
    if (window.matchMedia('(hover: none)').matches) return;

    const rect = ref.current.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / (rect.width / 2);
    const dy = (e.clientY - cy) / (rect.height / 2);

    ref.current.style.transform = `perspective(900px) rotateY(${dx * maxTilt}deg) rotateX(${-dy * maxTilt}deg) translateZ(8px)`;
    ref.current.style.transition = 'none';

    const highlight = ref.current.querySelector('.card-highlight');
    if (highlight) {
      highlight.style.background = `radial-gradient(circle at ${(dx + 1) * 50}% ${(dy + 1) * 50}%, rgba(255,255,255,0.08) 0%, transparent 60%)`;
      highlight.style.transition = 'none';
    }
  };

  const handleMouseLeave = () => {
    if (!ref.current) return;
    ref.current.style.transform = 'perspective(900px) rotateY(0deg) rotateX(0deg) translateZ(0px)';
    ref.current.style.transition = 'transform 0.5s cubic-bezier(0.23, 1, 0.32, 1)';
    const highlight = ref.current.querySelector('.card-highlight');
    if (highlight) {
      highlight.style.background = 'transparent';
      highlight.style.transition = 'background 0.5s cubic-bezier(0.23, 1, 0.32, 1)';
    }
  };

  return { ref, onMouseMove: handleMouseMove, onMouseLeave: handleMouseLeave };
}

export function useCountUp(end, duration = 1.4, inView = true) {
  const ref = useRef(null);
  const countUpRef = useRef(null);

  useEffect(() => {
    if (!ref.current) return;

    // Parse end value — guard against non-numeric strings like '—'
    const numericEnd = typeof end === 'number' ? end : parseFloat(end);
    const safeEnd = isNaN(numericEnd) ? 0 : numericEnd;

    if (inView) {
      // Re-create CountUp when target value changes
      countUpRef.current = new CountUp(ref.current, safeEnd, {
        duration,
        useEasing: true,
        useGrouping: true,
        separator: ',',
        decimalPlaces: safeEnd % 1 !== 0 ? 1 : 0,
      });
      if (!countUpRef.current.error) {
        countUpRef.current.start();
      }
    }
  }, [end, duration, inView]);

  return ref;
}

export function useIntersection(threshold = 0.1) {
  return useInView({ threshold, triggerOnce: true });
}

export function useScrollProgress() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - window.innerHeight;
      if (totalHeight > 0) {
        setProgress(window.scrollY / totalHeight);
      }
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return progress;
}

export function useParallax(speed = 0.2) {
  const { scrollY } = useScroll();
  return useTransform(scrollY, value => value * speed);
}
