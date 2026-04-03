export const expoOut = [0.16, 1, 0.3, 1];
export const sineOut = [0.39, 0.575, 0.565, 1];

export const softSpring = { type: 'spring', stiffness: 200, damping: 20, mass: 1 };
export const snappySpring = { type: 'spring', stiffness: 380, damping: 28, mass: 0.8 };
export const bouncySpring = { type: 'spring', stiffness: 400, damping: 15, mass: 1 };

export const fadeUp = {
  initial: { opacity: 0, y: 28 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.6, ease: expoOut } },
  exit: { opacity: 0, y: -20, transition: { duration: 0.3, ease: expoOut } },
};

export const fadeLeft = {
  initial: { opacity: 0, x: -28 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.6, ease: expoOut } },
  exit: { opacity: 0, x: 20, transition: { duration: 0.3, ease: expoOut } },
};

export const fadeRight = {
  initial: { opacity: 0, x: 28 },
  animate: { opacity: 1, x: 0, transition: { duration: 0.6, ease: expoOut } },
  exit: { opacity: 0, x: -20, transition: { duration: 0.3, ease: expoOut } },
};

export const scaleIn = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: expoOut } },
  exit: { opacity: 0, scale: 0.95, transition: { duration: 0.3, ease: expoOut } },
};

export const staggerContainer = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.055,
      delayChildren: 0.1,
    },
  },
};

export const listItem = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.4, ease: expoOut } },
};

export const cardHover = {
  rest: { y: 0, scale: 1, transition: snappySpring },
  hover: { y: -3, scale: 1, transition: snappySpring },
  tap: { scale: 0.97, transition: snappySpring },
};

export const blurIn = {
  initial: { opacity: 0, filter: 'blur(8px)' },
  animate: { opacity: 1, filter: 'blur(0px)', transition: { duration: 0.6, ease: expoOut } },
};
