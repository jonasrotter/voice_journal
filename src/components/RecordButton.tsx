import { Microphone, Stop } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface RecordButtonProps {
  isRecording: boolean
  onStart: () => void
  onStop: () => void
  duration: number
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

export function RecordButton({ isRecording, onStart, onStop, duration }: RecordButtonProps) {
  return (
    <div className="flex flex-col items-center gap-4">
      <Button
        onClick={isRecording ? onStop : onStart}
        size="lg"
        className={cn(
          'relative h-20 w-20 rounded-full p-0 transition-all duration-300',
          isRecording
            ? 'bg-accent hover:bg-accent/90'
            : 'bg-accent hover:bg-accent/90 hover:scale-105'
        )}
      >
        {isRecording && (
          <>
            <span className="absolute inset-0 animate-ping rounded-full bg-accent opacity-75" />
            <span className="absolute inset-0 animate-pulse rounded-full bg-accent/50" />
          </>
        )}
        {isRecording ? (
          <Stop size={32} weight="fill" className="relative z-10" />
        ) : (
          <Microphone size={32} weight="fill" className="relative z-10" />
        )}
      </Button>
      {isRecording && (
        <div className="text-sm font-medium text-muted-foreground animate-in fade-in">
          {formatDuration(duration)}
        </div>
      )}
    </div>
  )
}
