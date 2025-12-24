'use client';

/**
 * To-Do card - Homework task tracker
 * - Compact state: Progress bar and 3 visible tasks
 * - Expanded modal: Full task list with sections
 * - Checkbox completion animations
 * - FIXED: Dark mode support + gray border on modal
 * - FIXED: Accessibility - focus trap, Escape key, focus restoration
 */

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Plus } from 'lucide-react';
import { Task } from '../lib/types';
import { tasks as initialTasks } from '../lib/mockData';
import { modalVariants, backdropVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';

// Font families - matching SessionCard
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export function ToDoCard() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [tasks, setTasks] = useState<Task[]>(initialTasks);
  const modalRef = useRef<HTMLDivElement>(null);

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen: isExpanded,
    onClose: () => setIsExpanded(false),
    modalRef,
  });

  const completedCount = tasks.filter(t => t.completed).length;
  const totalCount = tasks.length;
  const progressPercent = Math.round((completedCount / totalCount) * 100);

  const activeTasks = tasks.filter(t => !t.completed);
  const completedTasks = tasks.filter(t => t.completed);

  const toggleTask = (taskId: string) => {
    setTasks(tasks.map(t =>
      t.id === taskId ? { ...t, completed: !t.completed } : t
    ));
  };

  return (
    <>
      {/* Compact Card */}
      <motion.div
        onClick={() => setIsExpanded(true)}
        className="bg-gradient-to-br from-[#FFF5F0] to-[#FFF8F3] dark:from-[#2a2435] dark:to-[#1a1625] rounded-3xl p-6 cursor-pointer h-[280px] flex flex-col overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]"
        style={{
          boxShadow: '0 2px 16px rgba(90,185,180,0.15)'
        }}
        whileHover={{
          boxShadow: '0 4px 20px rgba(90,185,180,0.25)',
          y: -2
        }}
        transition={{ duration: 0.2 }}
      >
        <div className="flex flex-col mb-3 text-center">
          <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200">To-Do</h2>
        </div>

        {/* Progress Bar - percentage on left, bar on right */}
        <div className="flex items-center gap-3 mb-6">
          <span style={{ fontFamily: fontSans, fontSize: '13px', fontWeight: 500 }} className="text-gray-600 dark:text-gray-400 whitespace-nowrap">
            {progressPercent}%
          </span>
          <div className="flex-1 h-2 bg-gray-200 dark:bg-[#3d3548] rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-[#5AB9B4] to-[#B8A5D6] dark:from-[#a78bfa] dark:to-[#c084fc]"
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            />
          </div>
        </div>

        {/* Task List Preview */}
        <div className="space-y-3 flex-1">
          {tasks.slice(0, 3).map((task) => (
            <div key={task.id} className="flex items-start gap-3">
              <div
                className={`w-4 h-4 rounded-full border-2 flex-shrink-0 mt-0.5 ${
                  task.completed
                    ? 'bg-[#5AB9B4] dark:bg-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
                    : 'border-[#5AB9B4] dark:border-[#a78bfa]'
                }`}
              >
                {task.completed && (
                  <svg viewBox="0 0 16 16" fill="none" className="text-white">
                    <path
                      d="M13 4L6 11L3 8"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </div>
              <span
                style={{ fontFamily: fontSerif, fontSize: '13px', fontWeight: 300, lineHeight: 1.5 }}
                className={task.completed
                    ? 'line-through text-gray-400 dark:text-gray-600'
                    : 'text-gray-700 dark:text-gray-300'}
              >
                {task.text}
              </span>
            </div>
          ))}

          {tasks.length > 3 && (
            <p style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500 }} className="text-gray-500 dark:text-gray-500 pt-2">
              +{tasks.length - 3} more tasks
            </p>
          )}
        </div>
      </motion.div>

      {/* Expanded Modal - FIXED: Gray border added */}
      <AnimatePresence>
        {isExpanded && (
          <>
            <motion.div
              variants={backdropVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={() => setIsExpanded(false)}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[1000]"
            />

            <motion.div
              ref={modalRef}
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="fixed w-[800px] max-h-[85vh] bg-gradient-to-br from-[#FFF5F0] to-[#FFF8F3] dark:from-[#2a2435] dark:to-[#1a1625] rounded-3xl shadow-2xl p-8 z-[1001] overflow-y-auto border-2 border-[#E0DDD8] dark:border-gray-600"
              role="dialog"
              aria-modal="true"
              aria-labelledby="todo-title"
              style={{
                top: '50%',
                left: '50%'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setIsExpanded(false)}
                className="absolute top-6 right-6 w-11 h-11 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
              >
                <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </button>

              <div className="mb-6 pr-12 text-center">
                <h2 style={{ fontFamily: fontSerif, fontSize: '24px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-1">To-Do</h2>
                <p style={{ fontFamily: fontSans, fontSize: '13px', fontWeight: 500 }} className="text-gray-600 dark:text-gray-400">
                  {progressPercent}% complete ({completedCount}/{totalCount} tasks)
                </p>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-2 bg-gray-200 dark:bg-[#3d3548] rounded-full overflow-hidden mb-8">
                <motion.div
                  className="h-full bg-gradient-to-r from-[#5AB9B4] to-[#B8A5D6] dark:from-[#a78bfa] dark:to-[#c084fc]"
                  animate={{ width: `${progressPercent}%` }}
                  transition={{ duration: 0.4, ease: 'easeOut' }}
                />
              </div>

              {/* Active Tasks */}
              {activeTasks.length > 0 && (
                <div className="mb-8">
                  <h3 style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-600 dark:text-gray-400 mb-4">
                    Active Tasks
                  </h3>
                  <div className="space-y-4">
                    {activeTasks.map((task) => (
                      <div key={task.id} className="flex items-start gap-3 group">
                        <button
                          onClick={() => toggleTask(task.id)}
                          className="w-5 h-5 rounded-full border-2 border-[#5AB9B4] dark:border-[#a78bfa] flex-shrink-0 mt-0.5 hover:bg-[#5AB9B4]/10 dark:hover:bg-[#a78bfa]/10 transition-colors"
                        />
                        <div className="flex-1">
                          <p style={{ fontFamily: fontSerif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="text-gray-700 dark:text-gray-300">{task.text}</p>
                          <p style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500 }} className="text-gray-500 dark:text-gray-500 mt-1">
                            From: Session {task.sessionId.replace('s', '')} ({task.sessionDate})
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Completed Tasks */}
              {completedTasks.length > 0 && (
                <div>
                  <div className="h-px bg-gray-200 dark:bg-[#3d3548] mb-6" />
                  <h3 style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-600 dark:text-gray-400 mb-4">
                    Completed Tasks
                  </h3>
                  <div className="space-y-4">
                    {completedTasks.map((task) => (
                      <div key={task.id} className="flex items-start gap-3 opacity-60 group">
                        <button
                          onClick={() => toggleTask(task.id)}
                          className="w-5 h-5 rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] border-2 border-[#5AB9B4] dark:border-[#a78bfa] flex-shrink-0 mt-0.5 hover:opacity-80 transition-colors flex items-center justify-center"
                        >
                          <svg viewBox="0 0 20 20" fill="none" className="w-3 h-3 text-white">
                            <path
                              d="M16 6L8 14L4 10"
                              stroke="currentColor"
                              strokeWidth="2.5"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        </button>
                        <div className="flex-1">
                          <p style={{ fontFamily: fontSerif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="text-gray-700 dark:text-gray-400 line-through">{task.text}</p>
                          <p style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500 }} className="text-gray-500 dark:text-gray-500 mt-1">
                            From: Session {task.sessionId.replace('s', '')} ({task.sessionDate})
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
