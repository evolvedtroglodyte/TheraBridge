"use client";

import { motion, AnimatePresence } from "framer-motion";

interface LoadingOverlayProps {
  visible: boolean;
}

export function LoadingOverlay({ visible }: LoadingOverlayProps) {
  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="absolute inset-0 z-50 flex items-center justify-center rounded-2xl"
          style={{
            backgroundColor: "rgba(236, 234, 229, 0.85)", // Light mode cream with transparency
          }}
        >
          {/* Dark mode overlay */}
          <div className="absolute inset-0 dark:bg-[rgba(26,22,37,0.85)] dark:block hidden rounded-2xl" />

          {/* Spinner */}
          <div className="relative z-10">
            <div className="w-8 h-8 border-3 border-gray-300 dark:border-gray-600 border-t-gray-700 dark:border-t-gray-300 rounded-full animate-spin" />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
