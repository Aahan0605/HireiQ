import React, { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

const DASH_PREFIXES = [
  '/dashboard', '/analyze', '/candidates', '/candidate',
  '/settings', '/jobs', '/bias-report', '/compare',
];

export default function ConstellationBackground() {
  const canvasRef = useRef(null);
  const { pathname } = useLocation();

  const isAuthPage = DASH_PREFIXES.some(p => pathname.startsWith(p));

  useEffect(() => {
    if (isAuthPage) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Respect prefers-reduced-motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const particles = [];
    // If prefers-reduced-motion is true, disable or heavily reduce particles
    const particleCount = prefersReducedMotion ? 0 : Math.min(60, Math.floor((width * height) / 20000));
    const connectionDistance = 120;
    const mouse = { x: null, y: null, radius: 150 };

    class Particle {
      constructor() {
        this.x = Math.random() * width;
        this.y = Math.random() * height;
        this.vx = (Math.random() - 0.5) * 0.4;
        this.vy = (Math.random() - 0.5) * 0.4;
        this.radius = Math.random() * 2 + 1;
        const colors = ['rgba(16, 185, 129, 0.4)', 'rgba(56, 189, 248, 0.4)', 'rgba(139, 92, 246, 0.4)'];
        this.color = colors[Math.floor(Math.random() * colors.length)];
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;

        if (this.x < 0 || this.x > width) this.vx = -this.vx;
        if (this.y < 0 || this.y > height) this.vy = -this.vy;

        if (mouse.x !== null && mouse.y !== null) {
          const dx = mouse.x - this.x;
          const dy = mouse.y - this.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < mouse.radius) {
            const force = (mouse.radius - dist) / mouse.radius;
            this.x -= dx / dist * force * 0.8;
            this.y -= dy / dist * force * 0.8;
          }
        }
      }

      draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.shadowBlur = 4;
        ctx.shadowColor = this.color;
        ctx.fill();
        ctx.shadowBlur = 0;
      }
    }

    // Initialize particles
    for (let i = 0; i < particleCount; i++) {
      particles.push(new Particle());
    }

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const handleMouseMove = (e) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    const handleMouseLeave = () => {
      mouse.x = null;
      mouse.y = null;
    };

    window.addEventListener('resize', handleResize);
    if (!prefersReducedMotion) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseleave', handleMouseLeave);
    }

    const animate = () => {
      ctx.clearRect(0, 0, width, height);

      const gradient = ctx.createRadialGradient(width / 2, height / 2, 10, width / 2, height / 2, Math.max(width, height));
      gradient.addColorStop(0, '#0d0d1a');
      gradient.addColorStop(1, '#05050d');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, width, height);

      if (!prefersReducedMotion) {
        particles.forEach((p) => {
          p.update();
          p.draw();
        });

        for (let i = 0; i < particles.length; i++) {
          for (let j = i + 1; j < particles.length; j++) {
            const p1 = particles[i];
            const p2 = particles[j];
            const dx = p1.x - p2.x;
            const dy = p1.y - p2.y;
            const dist = Math.sqrt(dx * dx + dy * dy);

            if (dist < connectionDistance) {
              const alpha = (1 - dist / connectionDistance) * 0.15;
              ctx.beginPath();
              ctx.moveTo(p1.x, p1.y);
              ctx.lineTo(p2.x, p2.y);
              ctx.strokeStyle = `rgba(139, 92, 246, ${alpha})`;
              ctx.lineWidth = 0.5;
              ctx.stroke();
            }
          }
        }
        animationFrameId = requestAnimationFrame(animate);
      }
    };

    animate();

    return () => {
      if (animationFrameId) cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, [isAuthPage]);

  if (isAuthPage) return null;

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 block w-full h-full -z-10 pointer-events-none"
    />
  );
}
