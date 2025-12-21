import { useState, useRef, useEffect } from 'react'
import { Play, Pause, Trash, Sparkle } from '@phosphor-icons/react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import type { JournalEntry } from '@/lib/types'
import { getEmotionColor, getEmotionLabel } from '@/lib/ai-processing'
import { format } from 'date-fns'

interface JournalEntryCardProps {
  entry: JournalEntry
  onDelete: (id: string) => void
}

export function JournalEntryCard({ entry, onDelete }: JournalEntryCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [isPlaying, setIsPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  useEffect(() => {
    if (entry.audioBlob && !entry.audioUrl) {
      entry.audioUrl = URL.createObjectURL(entry.audioBlob)
    }

    return () => {
      if (entry.audioUrl && entry.audioBlob) {
        URL.revokeObjectURL(entry.audioUrl)
      }
    }
  }, [entry])

  const handlePlayPause = () => {
    if (!audioRef.current) {
      if (entry.audioUrl) {
        audioRef.current = new Audio(entry.audioUrl)
        audioRef.current.addEventListener('timeupdate', () => {
          if (audioRef.current) {
            const prog = (audioRef.current.currentTime / audioRef.current.duration) * 100
            setProgress(prog)
          }
        })
        audioRef.current.addEventListener('ended', () => {
          setIsPlaying(false)
          setProgress(0)
        })
      }
    }

    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause()
      } else {
        audioRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const formatDate = (timestamp: number) => {
    return format(new Date(timestamp), 'MMM d, yyyy • h:mm a')
  }

  return (
    <Card
      className="group cursor-pointer overflow-hidden transition-all duration-300 hover:shadow-lg"
      onClick={() => setIsExpanded(!isExpanded)}
    >
      <div className="p-4 md:p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <time className="text-sm text-muted-foreground">
                {formatDate(entry.createdAt)}
              </time>
              {entry.status === 'processing' && (
                <Badge variant="secondary" className="flex items-center gap-1">
                  <Sparkle size={12} weight="fill" />
                  Processing...
                </Badge>
              )}
              {entry.emotion && entry.status === 'completed' && (
                <Badge
                  style={{
                    backgroundColor: getEmotionColor(entry.emotion),
                    color: 'white',
                  }}
                  className="capitalize"
                >
                  {entry.emotion}
                </Badge>
              )}
            </div>
            {entry.summary && (
              <p className="text-base font-medium leading-relaxed line-clamp-2">
                {entry.summary}
              </p>
            )}
            {!entry.summary && entry.status === 'processing' && (
              <p className="text-sm text-muted-foreground italic">
                Generating summary...
              </p>
            )}
            {!entry.summary && entry.status === 'error' && (
              <p className="text-sm text-destructive italic">
                Processing failed. Please try again.
              </p>
            )}
          </div>

          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="ghost"
              size="icon"
              onClick={handlePlayPause}
              disabled={!entry.audioUrl}
            >
              {isPlaying ? (
                <Pause size={20} weight="fill" />
              ) : (
                <Play size={20} weight="fill" />
              )}
            </Button>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="ghost" size="icon" className="text-destructive">
                  <Trash size={20} />
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete this entry?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. This will permanently delete your journal
                    entry and all associated data.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => onDelete(entry.id)}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        {isPlaying && progress > 0 && (
          <div className="mt-4">
            <Progress value={progress} className="h-1" />
          </div>
        )}

        {isExpanded && entry.transcript && (
          <div
            className="mt-4 space-y-3 animate-in fade-in slide-in-from-top-2"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="h-px bg-border" />
            <div>
              <h4 className="text-sm font-semibold mb-2">Transcript</h4>
              <p className="text-sm leading-relaxed text-foreground/90">
                {entry.transcript}
              </p>
            </div>
            {entry.emotion && (
              <div>
                <h4 className="text-sm font-semibold mb-1">Emotional Tone</h4>
                <p className="text-sm text-muted-foreground">
                  {getEmotionLabel(entry.emotion)}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}
