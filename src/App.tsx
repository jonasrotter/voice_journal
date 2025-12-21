import { useState, useEffect } from 'react'
import { useKV } from '@github/spark/hooks'
import { Toaster, toast } from 'sonner'
import { RecordButton } from '@/components/RecordButton'
import { WaveformVisualizer } from '@/components/WaveformVisualizer'
import { JournalEntryCard } from '@/components/JournalEntryCard'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useAudioRecorder } from '@/hooks/use-audio-recorder'
import { processJournalEntry } from '@/lib/ai-processing'
import type { JournalEntry } from '@/lib/types'

function App() {
  const [entries, setEntries] = useKV<JournalEntry[]>('journal-entries', [])
  const { isRecording, duration, startRecording, stopRecording } = useAudioRecorder()
  const [isProcessing, setIsProcessing] = useState(false)

  const entriesList = entries || []

  const handleStartRecording = async () => {
    const success = await startRecording()
    if (!success) {
      toast.error('Unable to access microphone. Please check your permissions.')
    }
  }

  const handleStopRecording = async () => {
    const audioBlob = await stopRecording()
    
    if (!audioBlob) {
      toast.error('Recording failed. Please try again.')
      return
    }

    if (audioBlob.size < 1000) {
      toast.error('Recording too short. Please try again.')
      return
    }

    const newEntry: JournalEntry = {
      id: Date.now().toString(),
      audioBlob,
      status: 'processing',
      createdAt: Date.now(),
      duration
    }

    setEntries((currentEntries) => [newEntry, ...(currentEntries || [])])
    setIsProcessing(true)

    try {
      const processed = await processJournalEntry(newEntry)
      
      setEntries((currentEntries) =>
        (currentEntries || []).map((entry) =>
          entry.id === newEntry.id
            ? { ...entry, ...processed }
            : entry
        )
      )

      toast.success('Journal entry saved!')
    } catch (error) {
      console.error('Processing error:', error)
      setEntries((currentEntries) =>
        (currentEntries || []).map((entry) =>
          entry.id === newEntry.id
            ? { ...entry, status: 'error' as const }
            : entry
        )
      )
      toast.error('Processing failed, but your audio is saved.')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleDeleteEntry = (id: string) => {
    setEntries((currentEntries) => (currentEntries || []).filter((entry) => entry.id !== id))
    toast.success('Entry deleted')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-lavender/10">
      <Toaster position="top-center" />
      
      <div className="container mx-auto px-4 py-8 md:py-12 max-w-4xl">
        <header className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-semibold mb-3 text-primary tracking-tight">
            Voice Journal
          </h1>
          <p className="text-muted-foreground text-lg">
            Reflect through sound, understand through words
          </p>
        </header>

        <div className="flex flex-col items-center gap-6 mb-12">
          <WaveformVisualizer isRecording={isRecording} />
          <RecordButton
            isRecording={isRecording}
            onStart={handleStartRecording}
            onStop={handleStopRecording}
            duration={duration}
          />
          {isRecording && (
            <p className="text-sm text-muted-foreground animate-pulse">
              Speak your thoughts freely...
            </p>
          )}
          {isProcessing && !isRecording && (
            <p className="text-sm text-muted-foreground flex items-center gap-2">
              <span className="inline-block h-2 w-2 rounded-full bg-accent animate-pulse" />
              Processing your entry...
            </p>
          )}
        </div>

        <div className="space-y-4">
          {entriesList.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                Tap the microphone above to start journaling
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <h2 className="text-2xl font-semibold text-foreground">Your Reflections</h2>
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-4">
                  {entriesList.map((entry) => (
                    <JournalEntryCard
                      key={entry.id}
                      entry={entry}
                      onDelete={handleDeleteEntry}
                    />
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App