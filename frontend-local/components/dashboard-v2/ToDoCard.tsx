'use client';

import React, { useState, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, Plus, Archive, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ModalWrapper } from '@/components/dashboard-v2/shared';
import { toDoData, type ToDoTask } from '@/lib/mock-data/dashboard-v2';

// ============================================================================
// Types
// ============================================================================

interface ToDoCardProps {
  className?: string;
}

interface TaskItemProps {
  task: ToDoTask;
  onToggle: (id: string) => void;
  showSource?: boolean;
  isCompact?: boolean;
}

// ============================================================================
// Animation Variants
// ============================================================================

const taskItemVariants = {
  initial: { opacity: 0, x: -10 },
  animate: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.2, ease: 'easeOut' as const }
  },
  exit: {
    opacity: 0,
    x: 10,
    transition: { duration: 0.15 }
  },
};

const checkboxVariants = {
  unchecked: { scale: 1 },
  checked: {
    scale: [1, 1.2, 1],
    transition: { duration: 0.3, ease: 'easeOut' as const }
  },
};

const staggerContainerVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

// ============================================================================
// Custom Checkbox Component
// ============================================================================

interface CustomCheckboxProps {
  checked: boolean;
  onChange: () => void;
  label: string;
  id: string;
}

function CustomCheckbox({ checked, onChange, label, id }: CustomCheckboxProps) {
  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange();
  };

  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      aria-labelledby={`${id}-label`}
      onClick={handleClick}
      className={cn(
        'flex-shrink-0 w-4 h-4 rounded-full border-2 transition-all duration-200',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500 focus-visible:ring-offset-2',
        checked
          ? 'bg-teal-500 border-teal-500'
          : 'border-gray-300 dark:border-gray-600 hover:border-teal-400'
      )}
    >
      <motion.div
        variants={checkboxVariants}
        animate={checked ? 'checked' : 'unchecked'}
        className="w-full h-full flex items-center justify-center"
      >
        {checked && (
          <motion.svg
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            className="w-2.5 h-2.5 text-white"
            viewBox="0 0 12 12"
            fill="none"
          >
            <path
              d="M2 6L5 9L10 3"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </motion.svg>
        )}
      </motion.div>
      <span className="sr-only">{label}</span>
    </button>
  );
}

// ============================================================================
// Task Item Component
// ============================================================================

function TaskItem({ task, onToggle, showSource = false, isCompact = false }: TaskItemProps) {
  return (
    <motion.div
      layout
      variants={taskItemVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={cn(
        'flex items-start gap-3',
        isCompact ? 'py-1.5' : 'py-2'
      )}
    >
      <CustomCheckbox
        checked={task.completed}
        onChange={() => onToggle(task.id)}
        label={task.text}
        id={task.id}
      />
      <div className="flex-1 min-w-0">
        <p
          id={`${task.id}-label`}
          className={cn(
            'text-sm font-normal leading-tight transition-all duration-200',
            task.completed
              ? 'text-gray-400 dark:text-gray-500 line-through'
              : 'text-gray-700 dark:text-gray-300'
          )}
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          {task.text}
        </p>
        {showSource && task.sourceSession && (
          <p
            className="text-xs text-gray-400 dark:text-gray-500 mt-0.5"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            {task.sourceSession}
          </p>
        )}
      </div>
    </motion.div>
  );
}

// ============================================================================
// Carousel Dots Component
// ============================================================================

interface CarouselDotsProps {
  totalPages: number;
  currentPage: number;
}

function CarouselDots({ totalPages, currentPage }: CarouselDotsProps) {
  return (
    <div className="flex items-center justify-center gap-1.5 mt-3">
      {Array.from({ length: totalPages }).map((_, idx) => (
        <div
          key={idx}
          className={cn(
            'w-1.5 h-1.5 rounded-full transition-all duration-200',
            idx === currentPage
              ? 'bg-teal-500 w-3'
              : 'bg-gray-300 dark:bg-gray-600'
          )}
        />
      ))}
    </div>
  );
}

// ============================================================================
// Progress Bar Component
// ============================================================================

interface ProgressBarProps {
  percentage: number;
  showLabel?: boolean;
  completed?: number;
  total?: number;
}

function ProgressBar({ percentage, showLabel = false, completed, total }: ProgressBarProps) {
  return (
    <div className="w-full">
      {showLabel && completed !== undefined && total !== undefined && (
        <div className="flex items-center justify-between mb-2">
          <span
            className="text-xs font-medium text-gray-500 dark:text-gray-400"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            {completed} of {total} completed
          </span>
          <span
            className="text-xs font-medium text-teal-600 dark:text-teal-400"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            {Math.round(percentage)}%
          </span>
        </div>
      )}
      <div className="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{
            background: 'linear-gradient(90deg, #14b8a6 0%, #a855f7 100%)',
          }}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

// ============================================================================
// Main ToDoCard Component
// ============================================================================

export function ToDoCard({ className }: ToDoCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [tasks, setTasks] = useState<ToDoTask[]>([
    ...toDoData.active,
    ...toDoData.completed,
  ]);
  const [currentPage] = useState(0);

  // Calculate completion stats
  const stats = useMemo(() => {
    const completed = tasks.filter((t) => t.completed).length;
    const total = tasks.length;
    const percentage = total > 0 ? (completed / total) * 100 : 0;
    return { completed, total, percentage };
  }, [tasks]);

  // Separate active and completed tasks
  const { activeTasks, completedTasks } = useMemo(() => {
    const active = tasks.filter((t) => !t.completed);
    const completed = tasks.filter((t) => t.completed);
    return { activeTasks: active, completedTasks: completed };
  }, [tasks]);

  // Get preview tasks (first 3)
  const previewTasks = useMemo(() => {
    return tasks.slice(0, 3);
  }, [tasks]);

  // Calculate remaining tasks count
  const remainingCount = useMemo(() => {
    return Math.max(0, tasks.length - 3);
  }, [tasks]);

  // Toggle task completion
  const handleToggle = useCallback((id: string) => {
    setTasks((prev) =>
      prev.map((task) =>
        task.id === id ? { ...task, completed: !task.completed } : task
      )
    );
  }, []);

  // Handle add new task (placeholder)
  const handleAddTask = useCallback(() => {
    // Placeholder for future implementation
    console.log('Add new task');
  }, []);

  // Handle archive completed (placeholder)
  const handleArchiveCompleted = useCallback(() => {
    setTasks((prev) => prev.filter((t) => !t.completed));
  }, []);

  // Handle delete selected (placeholder)
  const handleDeleteSelected = useCallback(() => {
    // Placeholder for future implementation
    console.log('Delete selected tasks');
  }, []);

  return (
    <>
      {/* Compact Card */}
      <motion.div
        className={cn(
          'relative overflow-hidden cursor-pointer',
          'rounded-lg p-5',  // Sharp 8px corners
          'bg-white dark:bg-gray-900',  // Flat white background
          'border border-gray-200 dark:border-gray-700',  // Subtle gray border
          className
        )}
        style={{
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',  // Minimal shadow
        }}
        initial={{ y: 0 }}
        whileHover={{
          y: -2,
          transition: { duration: 0.2, ease: 'easeOut' }
        }}
        whileTap={{ scale: 0.99 }}
        onClick={() => setIsExpanded(true)}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsExpanded(true);
          }
        }}
        aria-label="Open to-do list details"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3
            className="font-normal text-base text-gray-800 dark:text-gray-200"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            To-Do
          </h3>
          <span
            className="text-sm font-medium text-teal-600 dark:text-teal-400"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            {Math.round(stats.percentage)}%
          </span>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <ProgressBar percentage={stats.percentage} />
        </div>

        {/* Task List Preview */}
        <motion.div
          variants={staggerContainerVariants}
          initial="initial"
          animate="animate"
          className="space-y-1"
        >
          <AnimatePresence mode="popLayout">
            {previewTasks.map((task) => (
              <TaskItem
                key={task.id}
                task={task}
                onToggle={handleToggle}
                isCompact
              />
            ))}
          </AnimatePresence>
        </motion.div>

        {/* Remaining Count */}
        {remainingCount > 0 && (
          <p
            className="text-xs text-gray-400 dark:text-gray-500 mt-2"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            +{remainingCount} more {remainingCount === 1 ? 'task' : 'tasks'}
          </p>
        )}

        {/* Carousel Dots */}
        <CarouselDots totalPages={3} currentPage={currentPage} />
      </motion.div>

      {/* Expanded Modal */}
      <ModalWrapper
        isOpen={isExpanded}
        onClose={() => setIsExpanded(false)}
        title="To-Do"
        titleIcon={<CheckCircle2 className="w-5 h-5 text-teal-600" />}
        className="max-w-md"
      >
        {/* Progress Section */}
        <div className="mb-6">
          <ProgressBar
            percentage={stats.percentage}
            showLabel
            completed={stats.completed}
            total={stats.total}
          />
        </div>

        {/* Active Tasks */}
        <div className="mb-6">
          <h4
            className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Active Tasks
          </h4>
          <motion.div
            variants={staggerContainerVariants}
            initial="initial"
            animate="animate"
            className="space-y-1"
          >
            <AnimatePresence mode="popLayout">
              {activeTasks.length > 0 ? (
                activeTasks.map((task) => (
                  <TaskItem
                    key={task.id}
                    task={task}
                    onToggle={handleToggle}
                    showSource
                  />
                ))
              ) : (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-sm text-gray-400 dark:text-gray-500 italic py-2"
                  style={{ fontFamily: 'Inter, sans-serif' }}
                >
                  All tasks completed!
                </motion.p>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* Divider */}
        {completedTasks.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-700 my-4" />
        )}

        {/* Completed Tasks */}
        {completedTasks.length > 0 && (
          <div className="mb-6">
            <h4
              className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              Completed
            </h4>
            <motion.div
              variants={staggerContainerVariants}
              initial="initial"
              animate="animate"
              className="space-y-1"
            >
              <AnimatePresence mode="popLayout">
                {completedTasks.map((task) => (
                  <TaskItem
                    key={task.id}
                    task={task}
                    onToggle={handleToggle}
                    showSource
                  />
                ))}
              </AnimatePresence>
            </motion.div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center gap-2 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button
            type="button"
            onClick={handleAddTask}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 rounded-lg',
              'text-sm font-medium',
              'bg-teal-50 dark:bg-teal-900/30',
              'text-teal-600 dark:text-teal-400',
              'hover:bg-teal-100 dark:hover:bg-teal-900/50',
              'transition-colors duration-200',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-teal-500'
            )}
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            <Plus className="w-4 h-4" />
            Add New Task
          </button>

          {completedTasks.length > 0 && (
            <button
              type="button"
              onClick={handleArchiveCompleted}
              className={cn(
                'flex items-center gap-1.5 px-3 py-2 rounded-lg',
                'text-sm font-medium',
                'bg-gray-100 dark:bg-gray-800',
                'text-gray-600 dark:text-gray-400',
                'hover:bg-gray-200 dark:hover:bg-gray-700',
                'transition-colors duration-200',
                'focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-500'
              )}
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              <Archive className="w-4 h-4" />
              Archive Completed
            </button>
          )}

          <button
            type="button"
            onClick={handleDeleteSelected}
            className={cn(
              'flex items-center gap-1.5 px-3 py-2 rounded-lg ml-auto',
              'text-sm font-medium',
              'bg-rose-50 dark:bg-rose-900/30',
              'text-rose-600 dark:text-rose-400',
              'hover:bg-rose-100 dark:hover:bg-rose-900/50',
              'transition-colors duration-200',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-rose-500'
            )}
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            <Trash2 className="w-4 h-4" />
            Delete Selected
          </button>
        </div>
      </ModalWrapper>
    </>
  );
}

export default ToDoCard;
