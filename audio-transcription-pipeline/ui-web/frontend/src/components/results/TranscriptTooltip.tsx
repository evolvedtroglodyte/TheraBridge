import { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface TranscriptTooltipProps {
  message: string;
  type: 'auto-scroll-enabled' | 'auto-scroll-disabled' | 'click-scroll-enabled' | 'click-scroll-disabled' | 'auto-scroll-paused';
  show: boolean;
  onHide: () => void;
}

const TOOLTIP_COLORS = {
  'auto-scroll-enabled': 'bg-green-500 text-white',
  'auto-scroll-disabled': 'bg-gray-500 text-white',
  'click-scroll-enabled': 'bg-blue-500 text-white',
  'click-scroll-disabled': 'bg-gray-500 text-white',
  'auto-scroll-paused': 'bg-yellow-500 text-white',
};

export default function TranscriptTooltip({ message, type, show, onHide }: TranscriptTooltipProps) {
  useEffect(() => {
    if (show) {
      const timer = setTimeout(() => {
        onHide();
      }, 3000); // Fade out after 3 seconds
      return () => clearTimeout(timer);
    }
  }, [show, onHide]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.3 }}
          className="fixed bottom-4 left-1/2 transform -translate-x-1/2 z-50"
        >
          <div className={`px-4 py-2 rounded-lg shadow-lg ${TOOLTIP_COLORS[type]}`}>
            <p className="text-sm font-medium">{message}</p>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
