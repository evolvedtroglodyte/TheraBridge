import { cn } from "@/lib/utils"

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Set to false to disable the shimmer animation
   * @default true
   */
  animated?: boolean;
}

const Skeleton = ({ className, animated = true, ...props }: SkeletonProps) => {
  return (
    <div
      className={cn(
        "bg-muted rounded-md",
        animated && "animate-pulse",
        className
      )}
      {...props}
    />
  )
}

export { Skeleton }
export type { SkeletonProps }
