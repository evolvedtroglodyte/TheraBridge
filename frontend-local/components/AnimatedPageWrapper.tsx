'use client';

import { motion } from 'framer-motion';
import { pageTransitionVariants } from '@/lib/animations';

interface AnimatedPageWrapperProps {
  children: React.ReactNode;
  delay?: number;
}

export function AnimatedPageWrapper({
  children,
  delay = 0
}: AnimatedPageWrapperProps) {
  return (
    <motion.div
      variants={pageTransitionVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={{
        duration: 0.3,
        ease: 'easeOut' as const,
        delay,
      }}
    >
      {children}
    </motion.div>
  );
}
